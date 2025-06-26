import socket
import threading
import time


class StunClient:
    def __init__(self):
        self.stun_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.client_id: int | None = None
        self.peer_addr: tuple[str, int] | None = None
        self.sending_addr: tuple[str, int] | None = None

        # Aalborg strato
        self.STUN_SERVER_ADDR: tuple[str, int] = ("130.225.37.157", 12345)

        # Lyngby
        # self.STUN_SERVER_ADDR: tuple[str, int] = ("130.225.74.242", 12345)

        # Server in Stockholm
        # self.STUN_SERVER_ADDR: tuple[str, int] = ("34.51.139.212", 12345)

        # Server in Tokyo
        # self.STUN_SERVER_ADDR: tuple[str, int] = ("34.85.33.23", 12345)

        self.HOLE_PUNCH_TRIES: int = 5
        self.hole_punched: bool = False

        self.running: bool = True
        self.relay: bool = False
        self.turn_mode: bool = False

    def register(self) -> None:
        try:
            self.stun_socket.sendto(b"REGISTER", self.STUN_SERVER_ADDR)
            response, _ = self.stun_socket.recvfrom(4096)
            self.client_id = int(response.decode().split()[1])
            print(f"Registered with ID: {self.client_id}")
        except Exception as e:
            print(f"Error during registration: {e}")

    def request_peer(self) -> None:
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

    def hole_punch(self) -> None:
        for _ in range(self.HOLE_PUNCH_TRIES):
            try:
                if not self.peer_addr:
                    continue
                self.stun_socket.sendto(b"HOLE", self.peer_addr)
            except Exception as e:
                print(f"Error sending HOLE punch message: {e}")
            time.sleep(0.1)

    def handle_server_messages(self, message) -> None:
        parts = message.split()

        if parts[1] == "CONNECT":
            _, _, peer_ip, peer_port = parts
            print(f"Received peer details: {peer_ip}:{peer_port}")
            self.peer_addr = (peer_ip, int(peer_port))
            self.sending_addr = self.peer_addr
            self.hole_punch()

        if parts[1] == "INVALID_ID":
            print("Invalid target ID.")

        if parts[1] == "HEARTBEAT":
            self.stun_socket.sendto(b"ALIVE", self.STUN_SERVER_ADDR)

        if parts[1] == "DISCONNECT":
            print("Server disconnected")
            self.stun_socket.close()
            self.running = False
            exit(0)

        if parts[1] == "CLIENTS":
            print(f"Clients connected: {message}")

        if parts[1] == "TURN_MODE":
            print("Turn mode activated.")
            self.sending_addr = self.STUN_SERVER_ADDR
            self.turn_mode = True
            self.min_buffer_size = 12
            self.hole_punched = True

    def handle_hole_punch_message(self) -> None:
        self.hole_punched = True
        print("Hole punched!")
        self.stun_socket.sendto(b"HOLE PUNCHED", self.STUN_SERVER_ADDR)

    @staticmethod
    def _run_in_thread(func, *args) -> threading.Thread:
        """General worker function to run a function in a thread"""
        thread = threading.Thread(target=func, args=args, daemon=True)
        thread.start()
        return thread
