import socket
import threading
import time
from tkinter import Message


class StunClient:

    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("", 0))

        self.client_id = None
        self.peer_addr = None

        self.SERVER_ADDR = ("130.225.37.157", 12345)

        self.HOLE_PUNCH_TRIES = 5
        self.hole_punched = False

        self.running = True
        self.relay = False

        self.command_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.command_addr = ("192.168.10.1", 8889)

        self.video_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.video_sock.bind(("0.0.0.0", 11111))

    def register(self):
        self.sock.sendto(b"REGISTER", self.SERVER_ADDR)
        response, _ = self.sock.recvfrom(4096)
        self.client_id = response.decode().split()[1]
        print(f"Registered with ID: {self.client_id}")

    def get_peer_addr(self):
        if self.peer_addr:
            return self.peer_addr

    def request_peer(self):
        self.sock.sendto(b"CHECK", self.SERVER_ADDR)
        peer_id = input("Enter peer ID: ")
        self.sock.sendto(f"REQUEST {peer_id}".encode(), self.SERVER_ADDR)

    def start_connection_listener(self):
        self.listen_thread = threading.Thread(target=self.listen, daemon=True)
        self.listen_thread.start()

    def listen(self):
        while self.running:
            data = self.sock.recv(4096)

            if not self.relay and self.hole_punched:
                self.sock.sendto(data, ("127.0.0.1", 27463))
                continue
            message = data.decode()

            if message.startswith("SERVER"):
                if message.split()[1] == "CONNECT":
                    _, _, peer_ip, peer_port = message.split()
                    print(f"Received peer details: {peer_ip}:{peer_port}")
                    self.peer_addr = (peer_ip, int(peer_port))
                    self.hole_punch()

                if message.split()[1] == "HEARTBEAT":
                    self.sock.sendto(b"ALIVE", self.SERVER_ADDR)

                if message.split()[1] == "DISCONNECT":
                    print("Server disconnected due to other client disconnection")
                    self.sock.close()
                    self.running = False

                if message.split()[1] == "CLIENTS":
                    print(f"Clients connected: {message}")

            if message.startswith("HOLE") and not self.hole_punched:
                self.hole_punched = True
                print("Hole punched!")
                self.sock.sendto(b"HOLE PUNCHED", self.SERVER_ADDR)

            if message.startswith("PEER"):
                # intended for the relay
                continue
            print(f"Received message: {message}")        
            self.command_sock.sendto(bytes(message, "utf-8"), self.command_addr)

    def hole_punch(self):
        for _ in range(self.HOLE_PUNCH_TRIES):
            self.sock.sendto(b"HOLE", self.peer_addr)
            time.sleep(0.1)

    def send_command(self, command, print_command=False, take_response=False):
        self.sock.sendto(command.encode(), self.peer_addr)

    def main(self):
        self.register()
        self.start_connection_listener()
        self.request_peer()


if __name__ == "__main__":
    client = StunClient()
    client.relay = True
    client.main()

    while client.running:
        if client.hole_punched:
            msg = client.video_sock.recv(4096)
            client.sock.sendto(msg, client.peer_addr)
