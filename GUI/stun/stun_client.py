import socket
import threading
import time


class StunClient:
    def __init__(self):
        self.stun_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.stun_socket.bind(("", 0))

        self.client_id = None
        self.peer_addr = None

        self.STUN_SERVER_ADDR = ("130.225.37.157", 12345)

        self.HOLE_PUNCH_TRIES = 5
        self.hole_punched = False

        self.running = True
        self.relay = False

    def register(self):
        self.stun_socket.sendto(b"REGISTER", self.STUN_SERVER_ADDR)
        response, _ = self.stun_socket.recvfrom(4096)
        self.client_id = response.decode().split()[1]
        print(f"Registered with ID: {self.client_id}")

    @staticmethod
    def run_in_thread(func, *args) -> threading.Thread:
        """General worker function to run a function in a thread"""
        thread = threading.Thread(target=func, args=args, daemon=True)
        thread.start()
        return thread

    def request_peer(self):
        self.stun_socket.sendto(b"CHECK", self.STUN_SERVER_ADDR)
        peer_id = input("Enter peer ID: ")
        self.stun_socket.sendto(f"REQUEST {peer_id}".encode(), self.STUN_SERVER_ADDR)

    def start_connection_listener(self):
        self.listen_thread = threading.Thread(target=self.listen, daemon=True)
        self.listen_thread.start()

    def hole_punch(self):
        for _ in range(self.HOLE_PUNCH_TRIES):
            self.stun_socket.sendto(b"HOLE", self.peer_addr)
            time.sleep(0.1)

    def main(self):
        self.register()
        self.start_connection_listener()
        self.request_peer()
