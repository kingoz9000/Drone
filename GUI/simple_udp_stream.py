import av
import threading
import numpy as np

class VideoReceiver:
    def __init__(self):
        self.current_frame = None
        self.frame_grab_timeout = 10
        self.VIDEO_ADDRESS = "udp://@0.0.0.0:11111"
        self.frame_thread = threading.Thread(target=self.grab_frames, daemon=True)
        self.lock = threading.Lock()

    def grab_frames(self):
        try:
            container = av.open(self.VIDEO_ADDRESS)  # Open the UDP stream
            print("Video stream opened successfully")
            
            for frame in container.decode(video=0):
                with self.lock:
                    self.current_frame = frame.to_ndarray(format='bgr24')
                print("Frame received")

        except Exception as e:
            print(f"Error opening video stream: {e}")

    def start(self):
        self.frame_thread.start()

