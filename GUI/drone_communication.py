import socket

class DroneCommunication:
    def __init__(self):
        """Initialize the DroneCommunication object and set running to True"""
        # Sending commands / Recieving response
        self.COMMAND_PORT: int = 8889
        self.COMMAND_ADDRESS: str = "192.168.10.1"
        self.COMMAND_SOCKET: socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Recieving state
        self.STATE_IP: tuple = ("0.0.0.0", 8890)
        self.STATE_SOCKET: socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.STATE_SOCKET.bind(self.STATE_IP)

        self.connect()

    def send_command(
        self, command: str, print_command: bool = True, take_response: bool = False
    ) -> str | None:
        """Sends a command to the drone by encoding first"""
        self.COMMAND_SOCKET.sendto(
            command.encode("utf-8"), (self.COMMAND_ADDRESS, self.COMMAND_PORT)
        )
        if take_response:
            response, _ = self.COMMAND_SOCKET.recvfrom(1024)
            print(f"Command '{command}': Recived the response: '{response.decode()}'")
            return response.decode()
        elif print_command:
            print(f"Command sent '{command}'")

    def connect(self) -> None:
        """Connects to the drone by starting SDK mode('command') and turning on the video stream('streamon')"""
        self.send_command("command")
        self.send_command("streamon")


    def stop(self) -> None:
        """Stops the drone by turning off the video stream("streamoff") and setting running to False"""
        self.running = False
        self.send_command("streamoff")
        self.send_command("reboot")

if __name__ == "__main__":
    drone: DroneCommunication = DroneCommunication()

    drone.main()
