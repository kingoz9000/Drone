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
        self.stats_refresh_rate = 0.5  # seconds

        # Communication with drone
        self.drone_command_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.drone_command_addr = ("192.168.10.1", 8889)

        self.drone_video_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.drone_video_socket.bind(("0.0.0.0", 11111))

        self.state = None
        self.response = None

    def register(self):
        self.stun_socket.sendto(b"REGISTER", self.STUN_SERVER_ADDR)
        response, _ = self.stun_socket.recvfrom(4096)
        self.client_id = response.decode().split()[1]
        print(f"Registered with ID: {self.client_id}")

    def get_peer_addr(self):
        if self.peer_addr:
            return self.peer_addr

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

    def listen(self):
        while self.running:
            data = self.stun_socket.recv(4096)

            if not self.relay and self.hole_punched:
                # Loopback for the operator
                flag = data[0]

                # Check if the first byte is 0 or 1
                # If 0 send to loopback (videofeed)
                if flag == 0:
                    data = data[1:]
                    self.stun_socket.sendto(data, ("127.0.0.1", 27463))
                    continue

                # Response
                elif flag == 1:
                    # Skal sendes til TKinter
                    self.state = data[1:]
                    continue

                # State
                elif flag == 2:
                    self.response = data[1:]
                    continue

            message = data.decode()

            if message.startswith("SERVER"):
                if message.split()[1] == "CONNECT":
                    _, _, peer_ip, peer_port = message.split()
                    print(f"Received peer details: {peer_ip}:{peer_port}")
                    self.peer_addr = (peer_ip, int(peer_port))
                    self.hole_punch()

                if message.split()[1] == "HEARTBEAT":
                    self.stun_socket.sendto(b"ALIVE", self.STUN_SERVER_ADDR)

                if message.split()[1] == "DISCONNECT":
                    print("Server disconnected due to other client disconnection")
                    self.stun_socket.close()
                    self.running = False

                if message.split()[1] == "CLIENTS":
                    print(f"Clients connected: {message}")

            if message.startswith("HOLE") and not self.hole_punched:
                self.hole_punched = True
                print("Hole punched!")
                self.stun_socket.sendto(b"HOLE PUNCHED", self.STUN_SERVER_ADDR)

            if message.startswith("PEER"):
                # intended for the relay
                continue
            print(f"Received message: {message}")
            self.send_command_to_drone(message, take_response=False)

    def hole_punch(self):
        for _ in range(self.HOLE_PUNCH_TRIES):
            self.stun_socket.sendto(b"HOLE", self.peer_addr)
            time.sleep(0.1)

    def send_command_to_relay(self, command, print_command=False, take_response=False):
        self.stun_socket.sendto(command.encode(), self.peer_addr)

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
        shifted = bytearray([prefix]) + data
        client.stun_socket.sendto(shifted, client.peer_addr)

    def state_socket_handler(self):
        state_addr = ("0.0.0.0", 8890)
        self.state_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.state_socket.bind(state_addr)
        while self.running:
            state = self.drone_video_socket.recv(4096)
            self.send_data_to_operator(state, prefix=2)
            time.sleep(self.stats_refresh_rate)

    def main(self):
        self.register()
        self.start_connection_listener()
        self.request_peer()


if __name__ == "__main__":
    client = StunClient()
    client.relay = True
    # Response from drone to the relay but not to the operator
    client.drone_command_socket.bind(("0.0.0.0", 9000))
    client.main()
    client.run_in_thread(client.state_socket_handler)

    while client.running:
        if client.hole_punched:
            msg = client.drone_video_socket.recv(4096)
            client.send_data_to_operator(msg)
