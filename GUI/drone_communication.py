import socket
import time


class DroneCommunication:
    def __init__(self, command_addr, command_returnport):
        # Addresses and ports for sending commands / Recieving response
        self.COMMAND_ADDR: tuple = command_addr
        self.COMMAND_SOCKET: socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.COMMAND_SOCKET.bind(("0.0.0.0", command_returnport))

        # Recieving state
        self.STATE_IP: tuple = ("0.0.0.0", 8890)
        self.STATE_SOCKET: socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.STATE_SOCKET.bind(self.STATE_IP)
        self.STATE_REFRESH_RATE = 1
        self.stats = {}

    def send_command(
        self, command: str, print_command: bool = True, take_response: bool = False
    ) -> str | None:
        """Sends a command to the drone by encoding first"""
        self.COMMAND_SOCKET.sendto(command.encode("utf-8"), self.COMMAND_ADDR)
        if take_response:
            self.COMMAND_SOCKET.settimeout(0.5)
            try:
                response = self.COMMAND_SOCKET.recv(1024).decode()
                # print(f"Command '{command}': Recived the response: '{response}'")
                return response
            except socket.timeout:
                print(f"Command '{command}': No response received within 0.5 seconds")
                return None
        elif print_command:
            print(f"Command sent '{command} IP: {self.COMMAND_ADDR}'")

    def wifi_state_socket_handler(self):
        
        while True:
            self.drone_stats = self.STATE_SOCKET.recv(4096).decode().strip().strip(";").split(";")
            
            for part in self.drone_stats:
                key, value = part.split(":")
                if "," in value:
                    self.stats[key] = tuple(map(float, value.split(",")))
                else:
                    try:
                        self.stats[key] = float(value) if "." in value else int(value)
                    except ValueError:
                        self.stats[key] = value
            time.sleep(self.STATE_REFRESH_RATE )


if __name__ == "__main__":
    drone = DroneCommunication()
