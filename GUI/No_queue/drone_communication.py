import socket
import threading
import numpy as np
import av
import time
from tello_tkinter import TelloTkinterStream
from PIL import Image, ImageTk


class DroneCommunication:
    def __init__(self):
        """Initialize the DroneCommunication object and set running to True"""

        # Sending commands / Recieving response
        self.COMMAND_PORT = 8889
        self.COMMAND_ADDRESS = "192.168.10.1"
        self.COMMAND_SOCKET = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.STATE_IP = ("0.0.0.0", 8890)
        self.STATE_SOCKET = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.STATE_SOCKET.bind(self.STATE_IP)
        
        # Video stream recieving
        self.VIDEO_PORT = 11111  # Video receiving port
        self.VIDEO_IP = "0.0.0.0"  # Listen on all interfaces
        self.VIDEO_ADDRESS = f"udp://@{self.VIDEO_IP}:{self.VIDEO_PORT}"
    
        
    def send_command(self, command: str) -> None:
        """Sends a command to the drone by encoding first"""
        self.COMMAND_SOCKET.sendto(
            command.encode("utf-8"), (self.COMMAND_ADDRESS, self.COMMAND_PORT)
        )
        #respone, _ = self.COMMAND_SOCKET.recvfrom(1024)
        #print(f"Command '{command}' Recived the response: '{respone.decode()}'")

    def listen_for_state(self):
        while True:
            response, _ = self.STATE_SOCKET.recvfrom(1024)
            print(response.decode())

    def connect(self):
        """Connects to the drone by starting SDK mode("command"") and turning on the video stream("streamon")"""
        self.send_command("command")
        self.send_command("streamon")

    def frame_grab(self):
        """Grabs frames from the video stream and appends them to the frames queue"""
        try:
            self.container = av.open(
                self.VIDEO_ADDRESS,
                timeout=20,
                format="h264",
                options={"fflags": "nobuffer"},
            )

        except av.error.ExitError as av_error:
            print(f"Error opening video stream: {av_error}")
            return
        
        for frame in self.container.decode(video=0):
            img = np.array(frame.to_image())
            if img is not None and img.size > 0:
                try:
                    # Convert the frame to an ImageTk object
                    img = Image.fromarray(img)
                    imgtk = ImageTk.PhotoImage(image=img)
                    self.tkinter_window.video_label.imgtk = imgtk
                    self.tkinter_window.video_label.config(image=imgtk)

                except Exception as e:
                    print(f"Error updating video frame: {e}")

    @staticmethod
    def run_in_thread(func, *args):
        """General worker function to run a function in a thread"""
        thread = threading.Thread(target=func, args=args, daemon=True)
        thread.start()
        return thread
    
    def cleanup(self):
        """Safely clean up resources and close the Tkinter window."""
        print("Shutting down...")

        self.send_command("streamoff")

        self.tkinter_window.root.quit()
        self.tkinter_window.root.destroy()


    def main(self):
        self.connect()
        time.sleep(1)
    
        self.run_in_thread(self.frame_grab)
        time.sleep(1)

        self.tkinter_window = TelloTkinterStream()

        self.tkinter_window.root.protocol("WM_DELETE_WINDOW", self.cleanup)
        self.tkinter_window.root.bind("q", lambda e: self.cleanup())

        self.run_in_thread(self.tkinter_window.root.mainloop())


if __name__ == "__main__":
    drone = DroneCommunication()

    drone.main()

