import socket
import time

import PIL
from PIL import Image, ImageOps

# Tello's IP and port
TELLO_IP = "192.168.10.1"
TELLO_PORT = 8889
TELLO_ADDRESS = (TELLO_IP, TELLO_PORT)

# Create a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


# Send a command to Tello
def send_command(command):
    try:
        sock.sendto(command.encode(), TELLO_ADDRESS)
        print(f"Sent: {command}")

        # Receive response
        response, _ = sock.recvfrom(1024)
        print(f"Response: {response.decode()}")

    except Exception as e:
        print(f"Error: {e}")


# Start SDK mode
send_command("command")
time.sleep(1)


# Open video stream from Tello
# video_url = "udp://0.0.0.0:11111"
TELLO_VID_IP = "0.0.0.0"
TELLO_VID_PORT = 11111
sock_vid = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock_vid.bind((TELLO_VID_IP, TELLO_VID_PORT))

# Enable video stream
send_command("streamon")
time.sleep(1)
# Check if the stream opened successfully
height, width = (int(960 / 2), int(720 / 2))

while True:
    data, addr = sock_vid.recvfrom(8192)
    print(len(data))

    # img = Image.frombuffer("RGB", (12, 12), data)
    # img.show()
    # break

# Stop video stream
send_command("streamoff")

# Close socket
sock.close()
