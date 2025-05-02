import logging
import socket
import threading
import time


class StunServer:

    def __init__(self):
        self.SERVER_IP = "0.0.0.0"
        self.SERVER_PORT = 12345
        self.clients = {}
        self.clients_lock = threading.Lock()
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_socket.bind((self.SERVER_IP, self.SERVER_PORT))

        self.client_timeout = 1
        self.next_client_id = 0
        self.heartbeat_on = True
        self.auto_connect_mode = True # Set this to False for manual connection mode

        self.logger = logging.getLogger(__name__)
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

        self.logger.info(f"Server listening on {self.SERVER_IP}:{self.SERVER_PORT}")

        self.stun_mode = True

    def get_client_id(self, addr):
        self.logger.debug(
            f"Searching for client with address {addr} in dictionary: {self.clients}"
        )
        with self.clients_lock:
            for k, v in self.clients.items():
                if v[0] == addr:
                    return k
            return None

    def heartbeat(self):
        lasttime = 0
        while self.heartbeat_on:
            curtime = time.time()
            if curtime - lasttime <= 3:
                continue

            clients_to_remove = []
            for k, v in self.clients.items():
                if v[2] < self.client_timeout:
                    try:
                        self.server_socket.sendto("SERVER HEARTBEAT".encode(), v[0])
                        self.logger.debug(f"Sent heartbeat to Client {k}")
                    except Exception as e:
                        self.logger.error(f"Failed to send heartbeat to Client {k}: {e}")
                    v[2] += 1
                    continue

                self.logger.info(f"Client {k} has disconnected")
                for k2, v2 in self.clients.items():
                    if v2[1] != k:
                        continue
                    try:
                        self.server_socket.sendto("SERVER DISCONNECT".encode(), v2[0])
                        self.logger.info(
                            f"Notified Client {k2} about disconnection of Client {k}"
                        )
                    except Exception as e:
                        self.logger.error(
                            f"Failed to send disconnect message to Client {k2}: {e}"
                        )
                    self.clients[k2][1] = None

                clients_to_remove.append(k)

            for k in clients_to_remove:
                self.stun_mode = False
                del self.clients[k]

            lasttime = curtime

    def exchange(self):
        while True:
            data, addr = self.server_socket.recvfrom(4096)

            # TURN-specific behavior
            if len(data) > 0 and data[0] == 8 and not self.stun_mode:
                self.handle_turn_data(data, addr)
                continue
            
            message = data.decode().strip()
            if message.startswith("REGISTER"):
                self.handle_register(addr, self.auto_connect_mode)

            elif message.startswith("DISCONNECT"):
                self.handle_disconnect(addr)

            elif message.startswith("REQUEST_TURN_MODE"):
                self.handle_turn_request(addr)

            elif message.startswith("ALIVE"):
                self.handle_alive_message(addr)

            elif message.startswith("HOLE PUNCHED"):
                self.logger.info(f"Hole punched with Client {self.get_client_id(addr)}")

            elif message.startswith("CHECK"):
                self.handle_check_message(addr)

            elif message.startswith("REQUEST"):
                self.handle_request_message(addr, message)

    def handle_turn_data(self, data, addr):
        sender_id = self.get_client_id(addr)
        if sender_id == 0:
            target_addr = self.clients[1][0]  # Send to Client 1
        elif sender_id == 1:
            target_addr = self.clients[0][0]  # Send to Client 0
        else:
            self.logger.error(f"Invalid sender ID: {sender_id}")
            return

        # Forward the message to the target client
        try:
            self.server_socket.sendto(data[1:], target_addr)
        except Exception as e:
            self.logger.error(
                f"Failed to relay message from Client {sender_id}: {e}"
            )


    def handle_register(self, addr, auto_connect_mode):
        with self.clients_lock:
            client_id = 0
            clients_copy = sorted(self.clients.keys())
            for idx, num in enumerate(clients_copy):
                if idx == num:
                    continue
                client_id = idx
                break
            else:
                client_id = len(self.clients)
            self.clients[client_id] = [addr, None, 0]

        try:
            self.server_socket.sendto(f"REGISTERED {client_id}".encode(), addr)
            self.logger.info(f"Client {client_id} registered from {addr}")
        except Exception as e:
            self.logger.error(
                f"Failed to send registration confirmation to {addr}: {e}"
            )

        # Auto-connect logic
        if auto_connect_mode and len(self.clients) == 2:
            client_ids = list(self.clients.keys())
            client1_id, client2_id = client_ids[0], client_ids[1]
            client1_addr, client2_addr = (
                self.clients[client1_id][0],
                self.clients[client2_id][0],
            )

            try:
                # Send connection details to both clients
                self.server_socket.sendto(
                    f"SERVER CONNECT {client2_addr[0]} {client2_addr[1]}".encode(),
                    client1_addr,
                )
                self.server_socket.sendto(
                    f"SERVER CONNECT {client1_addr[0]} {client1_addr[1]}".encode(),
                    client2_addr,
                )
                self.logger.info(
                    f"Automatically connected Client {client1_id} and Client {client2_id}"
                )
            except Exception as e:
                self.logger.error(f"Failed to auto-connect clients: {e}")

    def handle_disconnect(self, addr):
        print("Received disconnect message")
        for k in list(self.clients.keys()).copy():
            self.logger.info(f"Client {self.get_client_id(k)} disconnected")
            self.server_socket.sendto(
                "SERVER DISCONNECT".encode(), self.clients[k][0]
            )
            self.clients.pop(k)
        self.stun_mode = False

    def handle_turn_request(self, addr):
        self.logger.debug(
            f"Client {self.get_client_id(addr)} requested TURN mode"
        )

        # check connection with other client

        # if connection is ok, send TURN mode request
        self.switch_turn_mode()

    def handle_alive_message(self, addr):
        self.logger.debug(f"Client {self.get_client_id(addr)} is alive")
        client_id = self.get_client_id(addr)
        self.logger.debug(f"Client {client_id} is alive")
        if client_id is not None:
            self.clients[client_id][2] = 0

    def handle_check_message(self, addr):
        # send list of clients except the one who requested
        client_id = self.get_client_id(addr)
        clients_to_send = []
        for k, v in self.clients.items():
            if k != client_id:
                clients_to_send.append(
                    (k, v[0][0], v[0][1])
                )  # Append client ID, IP, and port
        try:
            if clients_to_send and not self.auto_connect_mode:
                self.logger.info(
                    f"Sending list of clients to Client {client_id}"
                )
                self.server_socket.sendto(
                    f"SERVER CLIENTS {clients_to_send}".encode(), addr
                )
            else:
                self.logger.info(f"No clients to send to Client {client_id}")
                self.server_socket.sendto("SERVER CLIENTS 0".encode(), addr)
        except Exception as e:
            self.logger.error(f"Failed to send client list to {addr}: {e}")

    def handle_request_message(self, addr, message):
        self.logger.debug(f"Received request from {addr}")
        _, target_id = message.split()
        if target_id.isdigit():
            target_id = int(target_id)
            current_client_id = self.get_client_id(addr)
        else:
            self.logger.error(f"Invalid target ID: {target_id}")
            self.server_socket.sendto("SERVER INVALID_ID".encode(), addr)
            return

        if target_id in self.clients:
            self.clients[current_client_id][1] = target_id
            target_addr = self.clients[target_id][0]

            try:
                if self.clients[target_id][1] == current_client_id:
                    # Send both clients each other's public IP and port
                    self.server_socket.sendto(
                        f"SERVER CONNECT {target_addr[0]} {target_addr[1]}".encode(),
                        addr,
                    )
                    self.server_socket.sendto(
                        f"SERVER CONNECT {addr[0]} {addr[1]}".encode(),
                        target_addr,
                    )
                    self.logger.info(
                        f"Exchanged details between Client {current_client_id} and Client {target_id}"
                    )
                else:
                    self.logger.info(
                        f"Client {current_client_id} requested Client {target_id}, but target not set reciprocally."
                    )
            except Exception as e:
                self.logger.error(f"Failed to send connection details: {e}")
        else:
            try:
                self.server_socket.sendto("NOT_FOUND".encode(), addr)
                self.logger.info(
                    f"Client {current_client_id} requested Client {target_id}, but target not found."
                )
            except Exception as e:
                self.logger.error(
                    f"Failed to send NOT_FOUND message to {addr}: {e}"
                )

    def switch_turn_mode(self):
        self.logger.debug("TURN mode active: relaying messages")
        # send "TURN MODE activated" to all clients

        for k, v in self.clients.items():
            try:
                self.server_socket.sendto("SERVER TURN_MODE".encode(), v[0])
                self.logger.info(f"Sent TURN mode activation to Client {k}")
            except Exception as e:
                self.logger.error(
                    f"Failed to send TURN mode activation to Client {k}: {e}"
                )
        self.heartbeat_on = False
        self.stun_mode = False
        pass


if __name__ == "__main__":
    server = StunServer()
    try:
        threading.Thread(target=server.heartbeat, daemon=True).start()
        server.exchange()
    except KeyboardInterrupt:
        server.logger.info("Shutting down server")
        server.server_socket.close()
