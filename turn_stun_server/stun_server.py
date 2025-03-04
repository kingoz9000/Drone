import socket

class StunServer:

    def __init__(self):
        self.SERVER_IP = "0.0.0.0"
        self.SERVER_PORT = 12345
        self.clients = {}
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_socket.bind((self.SERVER_IP, self.SERVER_PORT))
        print(f"Server listening on {self.SERVER_IP}:{self.SERVER_PORT}")


    def exchange(self):
        while True:
            data, addr = self.server_socket.recvfrom(1024)
            message = data.decode().strip()

            if message.startswith("REGISTER"):

                client_id = len(self.clients) 
                self.clients[client_id] = 
                self.server_socket.sendto(f"REGISTERED {self.clients}".encode(), addr)
                print(f"Client {client_id} registered from {addr}")

            elif message.startswith("REQUEST"):
                _, target_id = message.split()
                target_id = int(target_id)

                if target_id in self.clients:
                    for key, value in self.clients.items():
                        if addr == value[0]:
                            self.clients[key][1] = target_id
                    target_addr = self.clients[target_id]
                    requester_id = [k for k, v in self.clients.items() if v == addr][0]

                    # Send both clients each other's public IP and port
                    self.server_socket.sendto(f"SERVER CONNECT {target_addr[0]} {target_addr[1]}".encode(), addr)
                    self.server_socket.sendto(f"SERVER CONNECT {addr[0]} {addr[1]}".encode(), target_addr)
                    print(f"Exchanged details between Client {requester_id} and Client {target_id}")

                else:
                    self.server_socket.sendto("NOT_FOUND".encode(), addr)

if __name__ == "__main__":
    server = StunServer()
    server.exchange()
