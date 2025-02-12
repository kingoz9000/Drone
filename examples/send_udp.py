import socket
import time
import numpy as np
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

# Take off
#send_command("takeoff")
#time.sleep(5)

# Start video stream
send_command("streamon")
time.sleep(5)

# Setup UDP socket for video stream
video_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
video_sock.bind(("0.0.0.0", 11111))

# OpenCV window
cv2.namedWindow("Tello Stream", cv2.WINDOW_NORMAL)

while True:
    data, _ = video_sock.recvfrom(2048)
    np_data = np.frombuffer(data, dtype=np.uint8)
    frame = cv2.imdecode(np_data, cv2.IMREAD_COLOR)

    if frame is not None:
        cv2.imshow("Tello Stream", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

video_sock.close()
cv2.destroyAllWindows()

# Land
#send_command("land")

# Close socket
sock.close()

