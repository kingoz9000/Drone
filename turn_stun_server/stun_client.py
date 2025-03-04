import socket
import threading
import time

class StunClient:
    SERVER_IP = "130.225.37.157"
    SERVER_PORT = 12345

    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("", 0))  # Use ephemeral port
        self.client_id = None
        self.peer_ip = None
        self.peer_port = None

    def register(self):
        self.sock.sendto(b"REGISTER", (self.SERVER_IP, self.SERVER_PORT))
        response, _ = self.sock.recvfrom(1024)
        self.client_id = response.decode().split()[1]
        print(f"✅ Registered as Client {self.client_id}")

    def request_peer(self):
        peer_id = input("Enter peer ID: ")
        self.sock.sendto(f"REQUEST {peer_id}".encode(), (self.SERVER_IP, self.SERVER_PORT))

    def start_connection_listener(self):
        threading.Thread(target=self.listen_for_peer, daemon=True).start()

    def listen_for_peer(self):
        while True:
            data, addr = self.sock.recvfrom(1024)
            message = data.decode()

            if message.startswith("PEER"):
                _, self.peer_ip, peer_port = message.split()
                self.peer_port = int(peer_port)
                print(f"🔗 Connecting to peer at {self.peer_ip}:{self.peer_port}")
                self.hole_punch()
                print("✅ Hole punching complete. Start chatting!")

            else:
                print(f"📩 Received: {message}")

    def hole_punch(self):
        for _ in range(10):
            self.sock.sendto(b"HOLE_PUNCH", (self.peer_ip, self.peer_port))
            time.sleep(1)

    def listen_for_server_messages(self):
        while True:
            data, addr = self.sock.recvfrom(1024)
            message = data.decode()

            if message == "CHECK":
                print("Sending ALIVE message...")
                self.sock.sendto(b"ALIVE", addr)

            elif message == "ALIVE":
                print("IM ALIVE")

            print(f"📩 Received: {message}")

    def chat_loop(self):
        while True:
            msg = input("You: ")
            if msg == "CHECK":
                print("🕒 Checking round trip time...")
                self.sock.sendto(b"CHECK", (self.SERVER_IP, self.SERVER_PORT))
            self.sock.sendto(msg.encode(), (self.peer_ip, self.peer_port))

    def main(self):
        self.register()
        self.start_connection_listener()
        self.request_peer()
        threading.Thread(target=self.listen_for_server_messages, daemon=True).start()
        self.chat_loop()

if __name__ == "__main__":
    client = StunClient()
    client.main()

