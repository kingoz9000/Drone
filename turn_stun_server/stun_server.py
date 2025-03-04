import socket

class StunServer:

    def __init__(self):
        self.SERVER_IP = "0.0.0.0"
        self.SERVER_PORT = 12345
        self.clients = {}
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_socket.bind((self.SERVER_IP, self.SERVER_PORT))
        print(f"Server listening on {self.SERVER_IP}:{self.SERVER_PORT}")

    def get_client_id(self, addr):
        for k, v in self.clients.items():
            if v[0] == addr:
                return k
        return None

    def exchange(self):
        while True:
            data, addr = self.server_socket.recvfrom(1024)
            message = data.decode().strip()

            if message.startswith("REGISTER"):

                client_id = len(self.clients) 
                self.clients[client_id] = [addr, None]
                self.server_socket.sendto(f"REGISTERED {self.clients}".encode(), addr)
                print(f"Client {client_id} registered from {addr}")

            elif message.startswith("REQUEST"):
                _, target_id = message.split()
                target_id = int(target_id)
                current_client_id = self.get_client_id(addr)

                if target_id in self.clients:
                    self.clients[current_client_id][1] = target_id
                    target_addr = self.clients[target_id][0]

                    if self.clients[target_id][1] == current_client_id:
                        # Send both clients each other's public IP and port
                        self.server_socket.sendto(f"PEER {target_addr[0]} {target_addr[1]}".encode(), addr)
                        self.server_socket.sendto(f"PEER {addr[0]} {addr[1]}".encode(), target_addr)
                        print(f"Exchanged details between Client {current_client_id} and Client {target_id}")
                    else:
                        print(f"Client {current_client_id} requested Client {target_id}, but target not set reciprocally.")
                else:
                    self.server_socket.sendto("NOT_FOUND".encode(), addr)

if __name__ == "__main__":
    server = StunServer()
    server.exchange()
