import socket, time

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
        lasttime = 0
        while True:
            curtime = time.time()
            # run every 10 seconds
            if curtime - lasttime > 10:
                for k, v in self.clients.items():
                    if v[2] >= 10:
                        print(f"Client {k} has disconnected")
                        # send to the client which has k as a target
                        for k2, v2 in self.clients.items():
                            if v2[1] == k:
                                self.server_socket.sendto(f"SERVER DISCONNECT".encode(), v2[0])
                                self.clients[k2][1] = None

                        del self.clients[k]
                    else:
                        print("Sending heartbeat to client", k)
                        self.server_socket.sendto(f"SERVER HEARTBEAT".encode(), v[0])
                        v[2] += 1
                lasttime = curtime

            data, addr = self.server_socket.recvfrom(1024)
            message = data.decode().strip()

            if message.startswith("REGISTER"):

                client_id = len(self.clients) 
                self.clients[client_id] = [addr, None, 0]
                self.server_socket.sendto(f"REGISTERED {self.clients}".encode(), addr)
                print(f"Client {client_id} registered from {addr}")

            elif message.startswith("ALIVE"):
                client_id = self.get_client_id(addr)
                if client_id is not None:
                    print(f"Client {client_id} is alive")
                    self.clients[client_id][2] = 0

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
                        print(f"Exchanged details between Client {current_client_id} and Client {target_id}")
                    else:
                        print(f"Client {current_client_id} requested Client {target_id}, but target not set reciprocally.")
                else:
                    self.server_socket.sendto("NOT_FOUND".encode(), addr)

if __name__ == "__main__":
    server = StunServer()
    server.exchange()
