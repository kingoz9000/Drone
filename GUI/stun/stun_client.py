import socket
import threading
import time
from tkinter import Message


class StunClient:

    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("", 0))  # Use ephemeral port

        self.client_id = None

        self.peer_addr = None

        self.SERVER_ADDR = ("130.225.37.157", 12345)

        self.HOLE_PUNCH_TRIES = 5
        self.hole_punched = False

        self.running = True

    def register(self):
        self.sock.sendto(b"REGISTER", self.SERVER_ADDR)
        response, _ = self.sock.recvfrom(4096)
        self.client_id = response.decode().split()[1]
        print(f"Registered with ID: {self.client_id}")

    def get_peer_addr(self):
        if self.peer_addr:
            return self.peer_addr

    def request_peer(self):  # Perhaps add assumeability for port id 0/1 for Pie.py
        self.sock.sendto(b"CHECK", self.SERVER_ADDR)
        peer_id = input("Enter peer ID: ")

        self.sock.sendto(f"REQUEST {peer_id}".encode(), self.SERVER_ADDR)

    def start_connection_listener(self):
        self.listen_thread = threading.Thread(target=self.listen, daemon=True)
        self.listen_thread.start()

    def listen(self):
        while self.running:
            data, addr = self.sock.recvfrom(4096)
            if self.hole_punched and addr == self.peer_addr:
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
                    self.running = False
                    self.sock.close()

                if message.split()[1] == "CLIENTS":
                    print(f"Clients connected: {message}")

            if message.startswith("HOLE") and not self.hole_punched:
                self.hole_punched = True
                print("Hole punched!")
                self.sock.sendto(b"HOLE PUNCHED", self.SERVER_ADDR)
                self.listen_thread.join()

            # Disliked, not sure how to refactor as i dont want peer communication to go through here, but i dont know how to avoid it
            if message.startswith("PEER"):
                print(f"\nPeer: {message.split()[1]}")
            print(message)

    def hole_punch(self):
        for _ in range(self.HOLE_PUNCH_TRIES):
            self.sock.sendto(b"HOLE", self.peer_addr)
            time.sleep(0.1)

    def chat_loop(self):
        while self.running:
            msg = input("You: ")
            msg = f"PEER {msg}"
            self.sock.sendto(msg.encode(), self.peer_addr)
        print("Chat loop stopped")

    def send_command(self, command, print_command=False, take_response=False):
        self.sock.sendto(command.encode(), self.peer_addr)

    def main(self):
        self.register()
        self.start_connection_listener()
        self.request_peer()


if __name__ == "__main__":
    client = StunClient()
    client.main()

    while client.running:
        if client.hole_punched:
            break
    client.chat_loop()
