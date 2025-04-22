import queue, threading, av, time, numpy as np


class DroneVideoFeed:
    def __init__(self, video_addr):
        # Video stream recieving
        self.VIDEO_ADDRESS: str = f"udp://@{video_addr[0]}:{str(video_addr[1])}"

        # Settings for frame grab & frame_queue
        self.frame_grab_timeout: int = 1
        self.frames_queue = queue.Queue(maxsize=5)

        self.run_in_thread(self.frame_grab)

    def frame_grab(self) -> None:
        """Grabs frames from the video stream and appends them to the frames queue"""
        try:
            self.container = av.open(
                self.VIDEO_ADDRESS,
                timeout=(self.frame_grab_timeout, None),
                format="h264",
                options={
                    # "fflags": "nobuffer",
                    "rtsp_transport": "udp",
                    # "reorder_queue_size": "0",
                    # "flush_packets": "1",
                    # "max_delay": "0",
                    "hwaccel": "auto",
                },
            )
        except av.error.ExitError as av_error:
            print(f"Error opening video stream: {av_error}")
            return

        try:
            for frame in self.container.decode(video=0):
                img = np.array(frame.to_image())
                if img is not None and img.size > 0:
                    try:
                        if not self.frames_queue.full():
                            self.frames_queue.put_nowait(
                                img
                            )  # Store only the latest frame
                        else:
                            self.frames_queue.get_nowait()  # Drop old frame
                            self.frames_queue.put_nowait(img)
                    except queue.Full:
                        pass
        except Exception as e:
            print(e)
            print("Trying again...")
            self.container.close()
            time.sleep(1)

            self.frame_grab()

    def get_frame(self) -> np.ndarray | None:
        """Returns the last frame in the frames queue"""
        if not self.frames_queue.empty():
            return self.frames_queue.get_nowait()
        return None

    @staticmethod
    def run_in_thread(func, *args) -> threading.Thread:
        """General worker function to run a function in a thread"""
        thread = threading.Thread(target=func, args=args, daemon=True)
        thread.start()
        return thread
