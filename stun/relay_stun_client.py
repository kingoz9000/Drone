import socket
import time

from .stun_client import StunClient


class RelayStunClient(StunClient):
    def __init__(self):
        super().__init__()
        self.drone_command_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.drone_command_addr: tuple[str, int] = ("192.168.10.1", 8889)

        self.drone_video_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.drone_video_socket.bind(("0.0.0.0", 11111))

        self.state: str | None = None
        self.response: bytes | None = None

        self.stats_refresh_rate: float = 0.5  # seconds

    def send_command_to_drone(self, command, take_response=False) -> None:
        self.drone_command_socket.sendto(
            bytes(command, "utf-8"), self.drone_command_addr
        )
        if take_response:
            self.drone_command_socket.settimeout(0.5)
            try:
                response = self.drone_command_socket.recv(1024)
                self.send_data_to_operator(response, prefix=2)
            except socket.timeout:
                print(f"Command '{command}': No response received within 0.5 seconds")

    def send_data_to_operator(self, data, prefix=0) -> None:
        if self.turn_mode:
            shifted = bytearray([16 + prefix]) + data
        else:
            shifted = bytearray([prefix]) + data

        if not self.sending_addr:
            return

        self.stun_socket.sendto(shifted, self.sending_addr)

    def state_socket_handler(self) -> None:
        state_addr = ("0.0.0.0", 8890)
        self.state_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.state_socket.bind(state_addr)
        while self.running:
            state = self.state_socket.recv(4096)
            self.send_data_to_operator(state, prefix=3)
            time.sleep(self.stats_refresh_rate)

    def bandwidth_tester(self, size=1024, interval=0.1) -> None:
        # interval 0.1 = 10 packets per second
        while self.running:
            data = bytearray([0] * size)
            self.send_data_to_operator(data, prefix=4)
            time.sleep(interval)

    def listen(self) -> None:
        while self.running:
            data = self.stun_socket.recv(4096)

            # Not confident it will find self.handle_flags, tho it is set
            message = data.decode()

            if message.startswith("SERVER"):
                self.handle_server_messages(message)
                continue

            if message.startswith("HOLE") and not self.hole_punched:
                self.handle_hole_punch_message()
                continue

            if message == "battery?":
                self.send_command_to_drone(message, take_response=True)
                continue
            self.send_command_to_drone(message, take_response=False)

    def main(self) -> None:
        self.register()
        self._run_in_thread(self.listen)
