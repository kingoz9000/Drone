import socket
import time

import cv2

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

# Enable video stream
send_command("streamon")
time.sleep(1)

# Open video stream from Tello
video_url = "udp://@0.0.0.0:11111"
cap = cv2.VideoCapture(video_url)

# Check if the stream opened successfully
if not cap.isOpened():
    print("❌ Error: Unable to open video stream")
    exit()

while True:
    ret, frame = cap.read()
    if not ret:
        print("❌ Failed to grab frame")
        continue

    cv2.imshow("Tello Stream", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

# Cleanup
cap.release()
cv2.destroyAllWindows()

# Stop video stream
send_command("streamoff")

# Close socket
sock.close()
