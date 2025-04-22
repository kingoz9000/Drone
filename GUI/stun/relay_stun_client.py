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
                response = self.drone_command_socket.recv(1024).decode()
                self.send_data_to_operator(response, prefix=1)
            except socket.timeout:
                print(f"Command '{command}': No response received within 0.5 seconds")

    def send_data_to_operator(self, data, prefix=0):
        shifted = bytearray([prefix]) + data.encode()
        if not self.peer_addr:
            return
        self.stun_socket.sendto(shifted, self.peer_addr)

    def state_socket_handler(self):
        state_addr = ("0.0.0.0", 8890)
        self.state_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.state_socket.bind(state_addr)
        while self.running:
            state = self.drone_video_socket.recv(4096)
            self.send_data_to_operator(state, prefix=2)
            time.sleep(self.stats_refresh_rate)

    def listen(self):
        while self.running:
            data = self.stun_socket.recv(4096)

            message = data.decode()

            if message.startswith("SERVER"):
                parts = message.split()
                if parts[1] == "CONNECT":
                    _, _, peer_ip, peer_port = parts
                    print(f"Received peer details: {peer_ip}:{peer_port}")
                    self.peer_addr = (peer_ip, int(peer_port))
                    self.hole_punch()
                    continue

                elif parts[1] == "HEARTBEAT":
                    self.stun_socket.sendto(b"ALIVE", self.STUN_SERVER_ADDR)
                    continue

                elif parts[1] == "DISCONNECT":
                    print("Server disconnected.")
                    self.stun_socket.close()
                    self.running = False
                    continue

                elif parts[1] == "CLIENTS":
                    print(f"Clients connected: {message}")
                    continue

            elif message.startswith("HOLE") and not self.hole_punched:
                self.hole_punched = True
                print("Hole punched!")
                self.stun_socket.sendto(b"HOLE PUNCHED", self.STUN_SERVER_ADDR)
                continue

            elif message == "battery?":
                self.send_command_to_drone(message, take_response=True)
                continue

            # This is command forwarding (from operator to drone)
            self.send_command_to_drone(message, take_response=False)


if __name__ == "__main__":
    client = RelayStunClient()
    client.relay = True
    # Response from drone to the relay but not to the operator
    client.drone_command_socket.bind(("0.0.0.0", 9000))
    client.main()
    client.run_in_thread(client.state_socket_handler)

    while client.running:
        if client.hole_punched:
            msg = client.drone_video_socket.recv(4096)
            client.send_data_to_operator(msg)
