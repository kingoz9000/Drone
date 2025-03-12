"""This is on the pie and isolated to the modem and it self"""

from socket import *
import threading
import time


class StunClient:

    def __init__(self):
        self.sock = socket(AF_INET, SOCK_DGRAM)
        self.sock.bind(("", 0))  # Use ephemeral port
        self.client_id = None
        self.peer_addr = None
        self.SERVER_ADDR = ("130.225.37.157", 12345)
        self.HOLE_PUNCH_TRIES = 5
        self.hole_punched = False

        self.command_sock = socket(AF_INET, SOCK_DGRAM)
        self.command_addr = ("192.168.10.1", 8889)

        self.video_sock = socket(AF_INET, SOCK_DGRAM)
        self.video_sock.bind(("0.0.0.0", 11111))

    def register(self):
        self.sock.sendto(b"REGISTER", self.SERVER_ADDR)
        response, _ = self.sock.recvfrom(1024)
        self.client_id = response.decode().split()[1]
        print(response.decode())

    def request_peer(self):
        peer_id = input("Enter peer ID: ")
        self.sock.sendto(f"REQUEST {peer_id}".encode(), self.SERVER_ADDR)

    def start_connection_listener(self):
        threading.Thread(target=self.listen, daemon=True).start()

    def listen(self):
        while True:
            data, addr = self.sock.recvfrom(4096)
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
                    break

            if message.startswith("HOLE") and not self.hole_punched:
                self.hole_punched = True
                print("Hole punched!")
                threading.Thread(target=self.chat_loop, daemon=True).start()

            if message.startswith("PEER"):
                print(f"Peer: {message.split()[1]}")
                self.command_sock.sendto(
                    bytes(message.split()[1], "utf-8"), self.command_addr
                )

    def hole_punch(self):
        for _ in range(self.HOLE_PUNCH_TRIES):
            self.sock.sendto(b"HOLE", self.peer_addr)
            time.sleep(0.1)

    def chat_loop(self):
        while True:
            msg = self.video_sock.recvfrom(4096)
            msg = f"PEER {msg}"
            self.sock.sendto(msg.encode(), self.peer_addr)

    def main(self):
        self.register()
        self.start_connection_listener()
        self.request_peer()
        while True:
            time.sleep(100)


if __name__ == "__main__":
    client = StunClient()
    client.main()
