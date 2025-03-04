import socket
import threading
import numpy as np
from collections import deque
import av
import time
import datetime


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

        # Video stream recieving
        self.VIDEO_PORT: int = 11111  # Video receiving port
        self.VIDEO_IP: int = "0.0.0.0"  # Listen on all interfaces
        self.VIDEO_ADDRESS: str = f"udp://@{self.VIDEO_IP}:{self.VIDEO_PORT}"

        # Settings for frame grab & frame_queue
        self.frame_grab_timeout: int = 5
        self.frame = None
        self.frame_available: bool = False
        self.running: bool = True

    def send_command(
        self, command: str, print_command: bool = True, take_response: bool = False
    ) -> str | None:
        """Sends a command to the drone by encoding first"""
        self.COMMAND_SOCKET.sendto(
            command.encode("utf-8"), (self.COMMAND_ADDRESS, self.COMMAND_PORT)
        )
        if take_response:
            response, _ = self.COMMAND_SOCKET.recvfrom(1024)
            print(
                f"Command '{command}': Recived the response: '{response.decode()}'"
            )
            return response
        elif print_command:
            print(f"Command sent '{command}'")

    def listen_for_state(self) -> None:
        while True:
            response, _ = self.STATE_SOCKET.recvfrom(1024)
            print(response.decode())

    def connect(self) -> None:
        """Connects to the drone by starting SDK mode('command') and turning on the video stream('streamon')"""
        self.send_command("command")
        self.send_command("streamon")

    def frame_grab(self) -> None:
        """Grabs frames from the video stream and appends them to the frames queue"""
        try:
            self.container = av.open(
                self.VIDEO_ADDRESS,
                timeout=(self.frame_grab_timeout, None),
                format="h264",
                options={
                    "fflags": "nobuffer",
                    "rtsp_transport": "udp",
                    "reorder_queue_size": "0",
                    "flush_packets": "1",
                },
            )
        except av.error.ExitError as av_error:
            print(f"Error opening video stream: {av_error}")
            return

        for frame in self.container.decode(video=0):
            if not self.running:
                break
            img = np.array(frame.to_image())
            if img is not None and img.size > 0:
                self.frame = img
                self.frame_available = True

    def get_frame(self) -> np.ndarray | None:
        """Returns the last frame in the frames queue"""
        if self.frame_available:
            self.frame_available = False
            return self.frame
        return None

    def stop(self) -> None:
        """Stops the drone by turning off the video stream("streamoff") and setting running to False"""
        self.running = False
        self.send_command("streamoff")

    @staticmethod
    def run_in_thread(func, *args) -> threading.Thread:
        """General worker function to run a function in a thread"""
        thread = threading.Thread(target=func, args=args, daemon=True)
        thread.start()
        return thread

    def main(self) -> None:
        self.connect()
        time.sleep(2)

        self.run_in_thread(self.frame_grab)
        time.sleep(2)

        # self.run_in_thread(self.listen_for_state)
        # time.sleep(2)


if __name__ == "__main__":
    drone: DroneCommunication = DroneCommunication()

    drone.main()
