import socket
import time

from .stun_client import StunClient


class RelayStunClient(StunClient):
    def __init__(self):
        super().__init__()
        self.drone_command_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.drone_command_addr = ("192.168.10.1", 8889)

        self.drone_video_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.drone_video_socket.bind(("0.0.0.0", 11111))

        self.state = None
        self.response = None

        self.stats_refresh_rate = 0.5  # seconds

    def send_command_to_drone(self, command, take_response=False):
        self.drone_command_socket.sendto(
            bytes(command, "utf-8"), self.drone_command_addr
        )
        if take_response:
            self.drone_command_socket.settimeout(0.5)
            try:
                response = self.drone_command_socket.recv(1024)
                self.send_data_to_operator(response, prefix=1)
            except socket.timeout:
                print(f"Command '{command}': No response received within 0.5 seconds")

    def send_data_to_operator(self, data, prefix=0):

        shifted = bytearray([prefix]) + data
        if self.turn_mode:
            shifted = bytearray([8]) + shifted

        if not self.sending_addr:
            return
        self.stun_socket.sendto(shifted, self.sending_addr)

    def state_socket_handler(self):
        state_addr = ("0.0.0.0", 8890)
        self.state_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.state_socket.bind(state_addr)
        while self.running:
            state = self.state_socket.recv(4096)
            self.send_data_to_operator(state, prefix=2)
            time.sleep(self.stats_refresh_rate)
