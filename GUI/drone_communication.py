import socket


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

        self.connect()

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

    def connect(self) -> None:
        """Connects to the drone by starting SDK mode('command') and turning on the video stream('streamon')"""
        self.send_command("command")
        self.send_command("streamon")

    def stop(self) -> None:
        """Stops the drone by turning off the video stream("streamoff")"""
        self.send_command("streamoff")


if __name__ == "__main__":
    drone = DroneCommunication()
