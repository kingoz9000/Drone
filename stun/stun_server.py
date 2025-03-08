import socket
import time 
import threading
import logging

class StunServer:

    def __init__(self):
        self.SERVER_IP = "0.0.0.0"
        self.SERVER_PORT = 12345
        self.clients = {}
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_socket.bind((self.SERVER_IP, self.SERVER_PORT))

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        stream_handler.setLevel(logging.DEBUG)
        self.logger.addHandler(stream_handler)

        file_handler = logging.FileHandler("stun_server.log")
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        file_handler.setLevel(logging.DEBUG)
        self.logger.addHandler(file_handler)

        self.logger.info(f"Server listening on {self.SERVER_IP}:{self.SERVER_PORT}")

    def get_client_id(self, addr):
        self.logger.debug(f"Searching for client with address {addr} in dictionary: {self.clients}")
        for k, v in self.clients.items():
            if v[0] == addr:
                return k
        return None


    def heartbeat(self):
        lasttime = 0
        while True:
            curtime = time.time()
            if curtime - lasttime > 5:
                clients_to_remove = []
                for k, v in self.clients.items():
                    if v[2] >= 3:
                        self.logger.info(f"Client {k} has disconnected")
                        for k2, v2 in self.clients.items():
                            if v2[1] == k:
                                self.server_socket.sendto(f"SERVER DISCONNECT".encode(), v2[0])
                                self.clients[k2][1] = None

                        clients_to_remove.append(k)
                    else:
                        self.server_socket.sendto(f"SERVER HEARTBEAT".encode(), v[0])
                        self.logger.debug(f"Sent heartbeat to Client {k}")
                        v[2] += 1

                for k in clients_to_remove:
                    del self.clients[k]

                lasttime = curtime


    def exchange(self):
        while True:
            data, addr = self.server_socket.recvfrom(1024)
            message = data.decode().strip()

            if message.startswith("REGISTER"):

                client_id = len(self.clients) 
                self.clients[client_id] = [addr, None, 0]
                self.server_socket.sendto(f"REGISTERED {client_id}".encode(), addr)
                self.logger.info(f"Client {client_id} registered from {addr}")

            elif message.startswith("ALIVE"):
                client_id = self.get_client_id(addr)
                self.logger.debug(f"Client {client_id} is alive")
                if client_id is not None:
                    self.clients[client_id][2] = 0

            elif message.startswith("CHECK"):
                # send list of clients except the one who requested
                client_id = self.get_client_id(addr)
                clients_to_send = []
                for k, v in self.clients.items():
                    if k != client_id:
                        clients_to_send.append((k, v[0][0], v[0][1]))  # Append client ID, IP, and port
                if clients_to_send:
                    self.logging.info(f"Sending list of clients to Client {client_id}")
                    self.server_socket.sendto(f"SERVER CLIENTS {clients_to_send}".encode(), addr)
                else:
                    self.logging.info(f"No clients to send to Client {client_id}")
                    self.server_socket.sendto("SERVER CLIENTS 0".encode(), addr)

            elif message.startswith("REQUEST"):
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
    threading.Thread(target=server.heartbeat).start()
    server.exchange()
