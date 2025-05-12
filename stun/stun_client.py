import socket
import threading
import time


class StunClient:
    def __init__(self):
        self.stun_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.client_id: int = None
        self.peer_addr: str = None
        self.sending_addr: tuple = None

        # Aalborg strato
        self.STUN_SERVER_ADDR: tuple[str, int] = ("130.225.37.157", 12345)

        # Lyngby
        # self.STUN_SERVER_ADDR: tuple[str, int] = ("130.225.74.242", 12345)

        # Server in Stockholm
        # self.STUN_SERVER_ADDR: tuple[str, int] = ("34.51.168.81", 12345)

        # Server in Tokyo
        # self.STUN_SERVER_ADDR: tuple[str, int] = ("34.85.33.23", 12345)

        self.HOLE_PUNCH_TRIES: int = 5
        self.hole_punched: bool = False

        self.running: bool = True
        self.relay: bool = False
        self.turn_mode: bool = False

    def register(self):
        try:
            self.stun_socket.sendto(b"REGISTER", self.STUN_SERVER_ADDR)
            response, _ = self.stun_socket.recvfrom(4096)
            self.client_id = response.decode().split()[1]
            print(f"Registered with ID: {self.client_id}")
        except Exception as e:
            print(f"Error during registration: {e}")

    def request_peer(self):
        try:
            self.stun_socket.sendto(b"CHECK", self.STUN_SERVER_ADDR)
        except Exception as e:
            print(f"Error sending CHECK message: {e}")
            return

        peer_id = input("Enter peer ID: ")
        try:
            self.stun_socket.sendto(
                f"REQUEST {peer_id}".encode(), self.STUN_SERVER_ADDR
            )
        except Exception as e:
            print(f"Error sending REQUEST message: {e}")

    def hole_punch(self):
        for _ in range(self.HOLE_PUNCH_TRIES):
            try:
                self.stun_socket.sendto(b"HOLE", self.peer_addr)
            except Exception as e:
                print(f"Error sending HOLE punch message: {e}")
            time.sleep(0.1)

    def listen(self):
        while self.running:
            data = self.stun_socket.recv(4096)

            # Not confident it will find self.handle_flags, tho it is set
            if not self.relay and self.handle_flags(data):
                continue

            message = data.decode()

            if message.startswith("SERVER"):
                parts = message.split()
                if parts[1] == "CONNECT":
                    _, _, peer_ip, peer_port = parts
                    print(f"Received peer details: {peer_ip}:{peer_port}")
                    self.peer_addr = (peer_ip, int(peer_port))
                    self.sending_addr = self.peer_addr
                    self.hole_punch()
                    continue

                if parts[1] == "INVALID_ID":
                    print("Invalid target ID.")
                    continue

                if parts[1] == "HEARTBEAT":
                    self.stun_socket.sendto(b"ALIVE", self.STUN_SERVER_ADDR)
                    continue

                if parts[1] == "DISCONNECT":
                    print("Server disconnected")
                    self.stun_socket.close()
                    self.running = False
                    exit(0)

                if parts[1] == "CLIENTS":
                    print(f"Clients connected: {message}")
                    continue

                if parts[1] == "TURN_MODE":
                    print("Turn mode activated.")
                    self.sending_addr = self.STUN_SERVER_ADDR
                    self.turn_mode = True
                    self.min_buffer_size = 10
                    self.hole_punched = True
                    continue

            if message.startswith("HOLE") and not self.hole_punched:
                self.hole_punched = True
                print("Hole punched!")
                self.stun_socket.sendto(b"HOLE PUNCHED", self.STUN_SERVER_ADDR)
                continue

            if self.relay:
                if message == "battery?":
                    self.send_command_to_drone(message, take_response=True)
                    continue
                self.send_command_to_drone(message, take_response=False)
            else:
                print("Unhanled command/message:", message)

    @staticmethod
    def _run_in_thread(func, *args) -> threading.Thread:
        """General worker function to run a function in a thread"""
        thread = threading.Thread(target=func, args=args, daemon=True)
        thread.start()
        return thread

    def main(self):
        self.register()
        self._run_in_thread(self.listen)
