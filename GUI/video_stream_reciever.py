import socket
import threading
import cv2
import numpy as np
import av
from collections import deque
import time

class DroneCommunication:
    def __init__(self):
        self.COMMAND_PORT = 8889
        self.COMMAND_ADDRESS = '192.168.10.1'
        self.COMMAND_SOCKET = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.VIDEO_PORT = 11111  # Video receiving port
        self.VIDEO_IP = "0.0.0.0"  # Listen on all interfaces
        self.VIDEO_ADDRESS = f"udp://@{self.VIDEO_IP}:{self.VIDEO_PORT}"
        self.frame_grab_timeout = 10
        self.frames = deque([], maxlen=60)  # Increase max buffer size
        self.running = True

    def send_command(self, command):
        self.COMMAND_SOCKET.sendto(command.encode('utf-8'), (self.COMMAND_ADDRESS, self.COMMAND_PORT))

    def connect(self):
        self.send_command("command")
        self.send_command("streamon")

    def frame_grab(self):
        """Grabs frames in a separate thread to improve speed."""
        try:
            self.container = av.open(self.VIDEO_ADDRESS, timeout=(self.frame_grab_timeout, None), format='h264', options={'fflags': 'nobuffer'})
        except av.error.ExitError as av_error:
            print(f"Error opening video stream: {av_error}")
            return

        for frame in self.container.decode(video=0):
            if not self.running:
                break
            img = np.array(frame.to_image())  # Convert frame to numpy
            if img is not None and img.size > 0:
                self.frames.append(img)

    def get_frame(self):
        """Return the latest frame if available, else return None."""
        if len(self.frames) > 0:
            return self.frames[-1]  # Return the latest frame (fast lookup)
        return None

    def stop(self):
        """Stop video streaming gracefully."""
        self.running = False
        self.send_command("streamoff")

    @staticmethod
    def run_in_thread(func, *args):
        thread = threading.Thread(target=func, args=args, daemon=True)
        thread.start()
        return thread

    def main(self):
        self.connect()
        self.run_in_thread(self.frame_grab)  # Run video processing in a thread

    def main(self):
        self.connect()
#        DroneCommunication.run_in_thread(self.recieve_response)
#        time.sleep(2)

        self.run_in_thread(self.frame_grab)
        time.sleep(2)

#        DroneCommunication.run_in_thread(self.manual_command_interface)
        #time.sleep(2)




if __name__ == "__main__":
    drone = DroneCommunication()

    drone.main()
