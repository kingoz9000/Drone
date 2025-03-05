import socket
import threading
import time

class StunClient:

    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("", 0))  # Use ephemeral port
        self.client_id = None
        self.peer_ip = None
        self.peer_port = None
        self.SERVER_IP = "130.225.37.157"
        self.SERVER_PORT = 12345
        self.HOLE_PUNCH_TRIES = 5
        self.hole_punched = False
        self.running = True

    def register(self):
        self.sock.sendto(b"REGISTER", (self.SERVER_IP, self.SERVER_PORT))
        response, _ = self.sock.recvfrom(1024)
        self.client_id = response.decode().split()[1]
        print(f"Registered with ID: {self.client_id}")

    def request_peer(self):
        peer_id = input("Enter peer ID: ")
        if peer_id == "CHECK":
            self.sock.sendto(b"CHECK", (self.SERVER_IP, self.SERVER_PORT))
            self.request_peer()
        self.sock.sendto(f"REQUEST {peer_id}".encode(), (self.SERVER_IP, self.SERVER_PORT))

    def start_connection_listener(self):
        threading.Thread(target=self.listen, daemon=True).start()

    def listen(self):
        while self.running:
            data, addr = self.sock.recvfrom(1024)
            message = data.decode()
            if message.startswith("SERVER"):
                if message.split()[1] == "CONNECT":
                    _, _, peer_ip, peer_port = message.split()
                    print(f"Received peer details: {peer_ip}:{peer_port}")
                    self.peer_ip = peer_ip
                    self.peer_port = int(peer_port)
                    self.hole_punch()

                if message.split()[1] == "HEARTBEAT":
                    self.sock.sendto(b"ALIVE", (self.SERVER_IP, self.SERVER_PORT))

                if message.split()[1] == "DISCONNECT":  
                    print("Server disconnected due to other client disconnection")
                    self.running = False
                if message.split()[1] == "CLIENTS":
                    print(f"Clients connected: {message}")
                    
                    
            
            if message.startswith("HOLE") and not self.hole_punched:
                self.hole_punched = True
                print("Hole punched!")
                threading.Thread(target=self.chat_loop, daemon=True).start()


            if message.startswith("PEER"):
                print(f"Peer: {message.split()[1]}")
                



    def hole_punch(self):
        for _ in range(self.HOLE_PUNCH_TRIES):
            self.sock.sendto(b"HOLE", (self.peer_ip, self.peer_port))
            time.sleep(0.1)


    def chat_loop(self):
        while self.running:
            msg = input("You: ")
            msg = f"PEER {msg}"
            self.sock.sendto(msg.encode(), (self.peer_ip, self.peer_port))

    def main(self):
        self.register()
        self.start_connection_listener()
        self.request_peer()
        while self.running:
            pass

if __name__ == "__main__":
    client = StunClient()
    client.main()
    print("Client stopped")

