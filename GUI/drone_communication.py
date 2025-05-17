import socket
import threading
import time


class LocalDroneCommunication:
    def __init__(self, command_addr, command_returnport) -> None:
        # Addresses and ports for sending commands / Recieving response
        self.COMMAND_ADDR: tuple = command_addr
        self.COMMAND_SOCKET: socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.COMMAND_SOCKET.bind(("0.0.0.0", command_returnport))

        # Recieving state
        self.STATE_IP: tuple = ("0.0.0.0", 8890)
        self.STATE_SOCKET: socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.STATE_SOCKET.bind(self.STATE_IP)
        self.STATE_REFRESH_RATE: int = 1
        self.stats: dict = {}
        self.stats_lock = threading.Lock()

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

    def get_direct_drone_stats(self) -> dict:
        with self.stats_lock:
            stats: dict = self.stats.copy()
        return stats

    def wifi_state_socket_handler(self) -> None:
        while True:
            self.drone_stats: list[str] = (
                self.STATE_SOCKET.recv(4096).decode().strip().strip(";").split(";")
            )

            for part in self.drone_stats:
                key, value = part.split(":")
                if "," in value:
                    with self.stats_lock:
                        self.stats[key] = tuple(map(float, value.split(",")))
                else:
                    try:
                        with self.stats_lock:
                            self.stats[key] = (
                                float(value) if "." in value else int(value)
                            )
                    except ValueError:
                        with self.stats_lock:
                            self.stats[key] = value
            time.sleep(self.STATE_REFRESH_RATE)


if __name__ == "__main__":
    drone = LocalDroneCommunication()
