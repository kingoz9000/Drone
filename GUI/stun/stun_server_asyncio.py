import asyncio
import logging
import time


class StunProtocol(asyncio.DatagramProtocol):
    def __init__(self):
        self.clients = {}  # client_id: [addr, target_id, missed_heartbeats]
        self.client_id_counter = 0
        self.clients_lock = asyncio.Lock()
        self.stun_mode = False
        self.transport = None

        self.logger = logging.getLogger("stun")
        self.logger.setLevel(logging.INFO)

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        )
        stream_handler.setLevel(logging.DEBUG)
        self.logger.addHandler(stream_handler)

        file_handler = logging.FileHandler("stun_server.log")
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        )
        file_handler.setLevel(logging.DEBUG)
        self.logger.addHandler(file_handler)

    def connection_made(self, transport):
        self.transport = transport
        self.logger.info("Async STUN server started")

        # Start heartbeat loop as a background task
        asyncio.create_task(self.heartbeat_loop())

    def datagram_received(self, data, addr):
        message = data.decode().strip()
        self.logger.debug(f"Received from {addr}: {message}")
        asyncio.create_task(self.handle_message(message, addr))

    async def handle_message(self, message, addr):
        if message.startswith("REGISTER"):
            async with self.clients_lock:
                client_id = self.client_id_counter
                self.clients[client_id] = [addr, None, 0]
                self.client_id_counter += 1
            self.transport.sendto(f"REGISTERED {client_id}".encode(), addr)
            self.logger.info(f"Client {client_id} registered from {addr}")

        elif message.startswith("ALIVE"):
            client_id = await self.get_client_id(addr)
            if client_id is not None:
                async with self.clients_lock:
                    self.clients[client_id][2] = 0
                self.logger.debug(f"Client {client_id} is alive")

        elif message.startswith("HOLE PUNCHED"):
            client_id = await self.get_client_id(addr)
            self.logger.info(f"Hole punched with Client {client_id}")
            self.stun_mode = True

        elif message.startswith("CHECK"):
            client_id = await self.get_client_id(addr)
            async with self.clients_lock:
                clients_to_send = [
                    (k, v[0][0], v[0][1])
                    for k, v in self.clients.items()
                    if k != client_id
                ]

            if clients_to_send:
                self.logger.info(f"Sending client list to Client {client_id}")
                self.transport.sendto(
                    f"SERVER CLIENTS {clients_to_send}".encode(), addr
                )
            else:
                self.logger.info(f"No clients to send to Client {client_id}")
                self.transport.sendto("SERVER CLIENTS 0".encode(), addr)

        elif message.startswith("REQUEST"):
            parts = message.split()
            if len(parts) != 2 or not parts[1].isdigit():
                self.logger.warning(f"Malformed REQUEST from {addr}: {message}")
                return

            target_id = int(parts[1])
            requester_id = await self.get_client_id(addr)

            async with self.clients_lock:
                if target_id in self.clients:
                    self.clients[requester_id][1] = target_id
                    target_addr = self.clients[target_id][0]

                    if self.clients[target_id][1] == requester_id:
                        # Mutual interest — exchange addresses
                        self.transport.sendto(
                            f"SERVER CONNECT {target_addr[0]} {target_addr[1]}".encode(),
                            addr,
                        )
                        self.transport.sendto(
                            f"SERVER CONNECT {addr[0]} {addr[1]}".encode(), target_addr
                        )
                        self.logger.info(
                            f"Connected Client {requester_id} and Client {target_id}"
                        )
                    else:
                        self.logger.info(
                            f"Client {requester_id} requested Client {target_id}, but not reciprocated"
                        )
                else:
                    self.transport.sendto("NOT_FOUND".encode(), addr)
                    self.logger.info(
                        f"Client {requester_id} requested unknown Client {target_id}"
                    )

    async def get_client_id(self, addr):
        async with self.clients_lock:
            for k, v in self.clients.items():
                if v[0] == addr:
                    return k
        return None

    async def heartbeat_loop(self):
        while True:
            await asyncio.sleep(5)
            to_remove = []

            async with self.clients_lock:
                for k, v in list(self.clients.items()):
                    if v[2] >= 3:
                        self.logger.info(f"Client {k} disconnected due to timeout")
                        # Notify peers
                        for k2, v2 in self.clients.items():
                            if v2[1] == k:
                                self.transport.sendto(
                                    "SERVER DISCONNECT".encode(), v2[0]
                                )
                                v2[1] = None
                        to_remove.append(k)
                    else:
                        self.transport.sendto("SERVER HEARTBEAT".encode(), v[0])
                        v[2] += 1

                for k in to_remove:
                    del self.clients[k]


async def main():
    loop = asyncio.get_running_loop()
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: StunProtocol(), local_addr=("0.0.0.0", 12345)
    )

    try:
        await asyncio.Event().wait()  # Keep running forever
    except KeyboardInterrupt:
        transport.close()
        print("Server shut down")


if __name__ == "__main__":
    asyncio.run(main())
