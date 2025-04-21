import cv2
import socket
import time
import av
import io

# Define the UDP IP and port
UDP_IP = "127.0.0.1"  # Change this to the IP where your DroneVideoFeed class is listening
UDP_PORT = 11112       # Same as used in your DroneVideoFeed setup

# Open a socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Load the video
video_path = "test_video.mp4"
cap = cv2.VideoCapture(video_path)

if not cap.isOpened():
    print("Error: Could not open video file.")
    exit()

# Create an AV container for encoding the video stream
class UDPSocketWriter(io.RawIOBase):
    def __init__(self, sock, addr):
        self.sock = sock
        self.addr = addr

    def writable(self):
        return True

    def write(self, b):
        self.sock.sendto(b, self.addr)
        return len(b)

udp_writer = UDPSocketWriter(sock, (UDP_IP, UDP_PORT))
container = av.open(udp_writer, format='h264', mode='w')

# Create a video stream and set properties (e.g., frame rate, resolution)
stream = container.add_stream('h264', rate=30)  # 30 FPS
stream.width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
stream.height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
stream.pix_fmt = 'yuv420p'


time.sleep(2)

# Main loop to read and send frames
while True:
    ret, frame = cap.read()
    
    if not ret:
        # Restart the video if it reaches the end
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        continue

    # Convert OpenCV frame to AV frame format
    av_frame = av.VideoFrame.from_ndarray(frame, format='bgr24')
    
    # Encode and send the frame to the UDP socket
    for packet in stream.encode(av_frame):
        container.mux(packet)

    # Simulate video frame rate (30 FPS)
    time.sleep(1 / 30)

# Flush the stream at the end
for packet in stream.encode():
    container.mux(packet)

cap.release()
container.close()
sock.close()
