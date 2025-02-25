import socket
import threading
import numpy as np
import av
from collections import deque
import time

class DroneCommunication:
    def __init__(self):
        """Initialize the DroneCommunication object and set running to True"""

        # Sending commands / Recieving response
        self.COMMAND_PORT = 8889
        self.COMMAND_ADDRESS = '192.168.10.1'
        self.COMMAND_SOCKET = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Video stream recieving
        self.VIDEO_PORT = 11111  # Video receiving port
        self.VIDEO_IP = "0.0.0.0"  # Listen on all interfaces
        self.VIDEO_ADDRESS = f"udp://@{self.VIDEO_IP}:{self.VIDEO_PORT}"

        # Settings for frame grab & frame_queue
        self.frame_grab_timeout = 10
        self.frames = deque([], maxlen=60)  
        self.running = True

    def send_command(self, command: str) -> None:
        """Sends a command to the drone by encoding first"""
        self.COMMAND_SOCKET.sendto(command.encode('utf-8'), (self.COMMAND_ADDRESS, self.COMMAND_PORT))

    def connect(self):
        """Connects to the drone by starting SDK mode("command"") and turning on the video stream("streamon")"""
        self.send_command("command")
        self.send_command("streamon")

    def frame_grab(self):
        """Grabs frames from the video stream and appends them to the frames queue"""
        try:
            self.container = av.open(self.VIDEO_ADDRESS, timeout=(self.frame_grab_timeout, None), format='h264', options={'fflags': 'nobuffer'})
        except av.error.ExitError as av_error:
            print(f"Error opening video stream: {av_error}")
            return

        for frame in self.container.decode(video=0):
            if not self.running:
                break
            img = np.array(frame.to_image())
            if img is not None and img.size > 0:
                self.frames.append(img)

    def get_frame(self):
        """Returns the last frame in the frames queue"""
        if len(self.frames) > 0:
            return self.frames[-1]  
        return None

    def stop(self):
        """Stops the drone by turning off the video stream("streamoff") and setting running to False"""
        self.running = False
        self.send_command("streamoff")

    @staticmethod
    def run_in_thread(func, *args):
        """General worker function to run a function in a thread"""
        thread = threading.Thread(target=func, args=args, daemon=True)
        thread.start()
        return thread


    def main(self):
        self.connect()
        time.sleep(2)

        self.run_in_thread(self.frame_grab)
        time.sleep(2)





if __name__ == "__main__":
    drone = DroneCommunication()

    drone.main()
