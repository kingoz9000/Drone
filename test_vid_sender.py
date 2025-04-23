import cv2
import socket
import struct

# Configuration
VIDEO_FILE = "testvideo.mp4"  # Replace with your video file path
LOOPBACK_IP = "127.0.0.1"
PORT = 5000
MAX_PACKET_SIZE = 65507  # Maximum UDP packet size

def main():
    # Open video file
    cap = cv2.VideoCapture(VIDEO_FILE)
    if not cap.isOpened():
        print("Error: Could not open video file.")
        return

    # Create a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Initialize sequence number
    sequence_number = 0

    while True:
        # Read a frame from the video
        ret, frame = cap.read()
        if not ret:
            print("End of video file.")
            break

        # Encode the frame as JPEG
        ret, encoded_frame = cv2.imencode('.jpg', frame)
        if not ret:
            print("Error: Could not encode frame.")
            continue

        # Convert the encoded frame to bytes
        frame_data = encoded_frame.tobytes()

        # Split the frame data into packets if necessary
        for i in range(0, len(frame_data), MAX_PACKET_SIZE - 1):
            # Extract a chunk of data
            chunk = frame_data[i:i + (MAX_PACKET_SIZE - 1)]

            # Prepend the sequence number (1 byte)
            packet = struct.pack("B", sequence_number) + chunk

            # Send the packet over the loopback device
            sock.sendto(packet, (LOOPBACK_IP, PORT))

            # Increment and wrap the sequence number
            sequence_number = (sequence_number + 1) % 256

    # Release resources
    cap.release()
    sock.close()

if __name__ == "__main__":
    main()