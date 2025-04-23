import cv2

# Tello's IP and port
TELLO_IP = "224.1.1.1"
TELLO_PORT = 54545
TELLO_ADDRESS = (TELLO_IP, TELLO_PORT)

# Open video stream from Tello
video_url = f"udp://@0.0.0.0:{TELLO_PORT}"
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

    cv2.imshow("Stream", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

# Cleanup
cap.release()
cv2.destroyAllWindows()
