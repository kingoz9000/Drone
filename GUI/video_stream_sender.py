"""Sends a video stream from webcam using port 11111 and a can recieve commands from port 8889"""

import socket
import threading
import cv2

class VideoSender:
    def __init__(self):

        self.reciver_ip = '172.25.252.243'
        # Create a socket object
        self.video_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.VIDEO_PORT = 11111
        self.COMMAND_PORT = 8889

        self.video_sender_thread = threading.Thread(target=self.send_video, daemon=True)
        self.command_reciever_thread = threading.Thread(target=self.recieve_command, daemon=True)

    def start(self):
        self.cap = cv2.VideoCapture(0)
        self.video_sender_thread.start()
        self.command_reciever_thread.start()

    def send_video(self):
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break

            # Serialize frame
            _, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 50])
            self.video_socket.sendto(buffer, (self.reciver_ip, self.VIDEO_PORT))

    def recieve_command(self):
        self.command_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.command_socket.bind(('0.0.0.0', self.COMMAND_PORT))
        while True:
            data, _ = self.command_socket.recvfrom(1024)
            print(data.decode('utf-8'))

if __name__ == '__main__':
    video_sender = VideoSender()
    video_sender.start()
    while True:
        pass
