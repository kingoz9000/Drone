import queue
import socket
import subprocess

import cv2


class WebserverSender:
    def __init__(self):
        self.FFMPEG_CMD = [
            "ffmpeg",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "bgr24",
            "-s",
            "640x480",
            "-r",
            "30",
            "-i",
            "-",
            "-vf",
            "format=yuv420p",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-tune",
            "zerolatency",
            "-x264-params",
            "keyint=30:min-keyint=30:scenecut=0",
            "-b:v",
            "800k",
            "-maxrate",
            "800k",
            "-bufsize",
            "1600k",
            "-f",
            "mpegts",
            "udp://130.225.37.157:27463?pkt_size=1316",
        ]

        self.WEBSERVER_IP = "130.225.37.157"
        self.WEBSERVER_PORT = 27463
        self.webserver_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.frame_queue = queue.Queue(maxsize=5)
        self.ffmpeg_process = self.ffmpeg_process = subprocess.Popen(
            self.FFMPEG_CMD, stdin=subprocess.PIPE
        )

    def ffmpeg_writer(self):
        while True:
            try:
                frame = self.frame_queue.get()
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                if self.ffmpeg_process.poll() is not None:
                    print("FFmpeg process exited.")
                    break
                self.ffmpeg_process.stdin.write(frame_rgb.tobytes())
            except Exception as e:
                print(f"FFmpeg stream error: {e}")
                break
