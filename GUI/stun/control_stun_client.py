from .stun_client import StunClient
from queue import Queue
import socket


class ControlStunClient(StunClient):
    def __init__(self):
        super().__init__()
        self.response = Queue()

    def send_command_to_relay(self, command, print_command=False, take_response=False):
        self.stun_socket.sendto(command.encode(), self.peer_addr)

    def get_peer_addr(self):
        if self.peer_addr:
            return self.peer_addr

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
                    self.response.put(data[1:])
                    continue

                # State
                elif flag == 2:
                    self.state = data[1:]
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
