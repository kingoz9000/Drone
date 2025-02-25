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
        self.frames = deque([], 30)

    def send_command(self, command):
        self.COMMAND_SOCKET.sendto(command.encode('utf-8'), (self.COMMAND_ADDRESS, self.COMMAND_PORT))

    def connect(self):
        self.send_command("command")
        self.send_command("streamon")

    def manual_command_interface(self):
        while True:
            command = input("Enter command: ")
            self.send_command(command)
            if command.lower() == "q":
                break

    def recieve_response(self):
        while True:
            try:
                data, addr = self.COMMAND_SOCKET.recvfrom(1024)
                print("Command Response:", data.decode("ASCII"))
            except Exception as e:
                print("Error receiving command response:", e)
                break

    def frame_grab(self):
        """Grabs the frames streamed by the drone"""
        try:
            self.container = av.open(self.VIDEO_ADDRESS, timeout=(self.frame_grab_timeout, None), format='h264', options={'fflags': 'nobuffer'})

        except av.error.ExitError as av_error:
            print(f"Error opening video stream.  {av_error}")
            return

        for frame in self.container.decode(video=0):
            img = frame.to_ndarray(format='bgr24')
            if img is not None and img.size > 0:
                self.frames.append(img)
            else:
                print("Empty frame received")

    def frame_updater(self):
        while True:
            if len(self.frames) > 0:
                self.current_frame = self.frames.popleft()
            else:
                self.current_frame = np.zeros((720, 960, 3), dtype=np.uint8)
            time.sleep(0.01)

    def video_show(self):
        """Displays current frame"""
        self.current_frame = np.zeros((720, 960, 3), dtype=np.uint8)
        DroneCommunication.run_in_thread(self.frame_updater)

        while True:
            cv2.imshow("Drone Video Stream", self.current_frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    @staticmethod
    def run_in_thread(func, *args):
        thread = threading.Thread(target=func, args=args, daemon=True)
        thread.start()
        return thread

    def main(self):
        self.connect()
        # Start receiving command responses
        DroneCommunication.run_in_thread(self.recieve_response)
        time.sleep(2)

        # Start receiving video stream
        DroneCommunication.run_in_thread(self.frame_grab)
        time.sleep(2)


        # Start manual command interface
        #DroneCommunication.run_in_thread(self.manual_command_interface)
        #time.sleep(2)

        self.video_show()

        while True:
            pass


if __name__ == "__main__":
    drone = DroneCommunication()

    drone.main()
