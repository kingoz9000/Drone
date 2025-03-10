import socket
import time
import logging

class StunServer:

    def __init__(self):
        self.SERVER_IP = "0.0.0.0"
        self.SERVER_PORT = 12345
        self.clients = {}
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_socket.bind((self.SERVER_IP, self.SERVER_PORT))

        self.logger = logging.getLogger("stun_server")
        self.logger.setLevel(logging.DEBUG)

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
        stream_handler.setLevel(logging.INFO)
        self.logger.addHandler(stream_handler)

        file_handler = logging.FileHandler("stun_server.log", mode="a")
        file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S"))
        file_handler.setLevel(logging.DEBUG)  
        self.logger.addHandler(file_handler)

        self.logger.info(f"Server listening on {self.SERVER_IP}:{self.SERVER_PORT}")

    def get_client_id(self, addr):
        self.logger.debug(f"Searching for client with address {addr} in dict: {self.clients}")
        for k, v in self.clients.items():
            if v[0] == addr:
                return k
        return None

    def exchange(self):
        lasttime = 0
        while True:
            curtime = time.time()
            # run every 10 seconds
            if curtime - lasttime > 10:
                for k, v in self.clients.items():
                    if v[2] >= 10:
                        self.logger.info(f"Client {k} has disconnected")
                        # send to the client which has k as a target
                        for k2, v2 in self.clients.items():
                            if v2[1] == k:
                                self.server_socket.sendto(f"SERVER DISCONNECT".encode(), v2[0])
                                self.clients[k2][1] = None
                                self.logger.info(f"Client {k2} disconnected from Client {k}")

                        del self.clients[k]
                    else:
                        self.server_socket.sendto(f"SERVER HEARTBEAT".encode(), v[0])
                        v[2] += 1
                lasttime = curtime

            data, addr = self.server_socket.recvfrom(1024)
            message = data.decode().strip()

            if message.startswith("REGISTER"):

                client_id = len(self.clients) 
                self.clients[client_id] = [addr, None, 0]
                self.server_socket.sendto(f"REGISTERED {self.clients}".encode(), addr)
                self.logger.info(f"Client {client_id} registered from {addr}")

            elif message.startswith("ALIVE"):
                self.logger.debug(f"Client {self.get_client_id(addr)} is alive")
                client_id = self.get_client_id(addr)
                if client_id is not None:
                    self.clients[client_id][2] = 0

            elif message.startswith("REQUEST"):
                self.logger.debug(f"Received request from {addr}")
                _, target_id = message.split()
                target_id = int(target_id)
                current_client_id = self.get_client_id(addr)

                if target_id in self.clients:
                    self.clients[current_client_id][1] = target_id
                    target_addr = self.clients[target_id][0]

                    if self.clients[target_id][1] == current_client_id:
                        # Send both clients each other's public IP and port
                        self.server_socket.sendto(f"SERVER CONNECT {target_addr[0]} {target_addr[1]}".encode(), addr)
                        self.server_socket.sendto(f"SERVER CONNECT {addr[0]} {addr[1]}".encode(), target_addr)
                        self.logger.info(f"Exchanged details between Client {current_client_id} and Client {target_id}")
                    else:
                        self.logger.info(f"Client {current_client_id} requested Client {target_id}, but target not set reciprocally.")
                else:
                    self.server_socket.sendto("NOT_FOUND".encode(), addr)
                    self.logger.info(f"Client {current_client_id} requested Client {target_id}, but target not found.")

if __name__ == "__main__":
    server = StunServer()
    server.exchange()
