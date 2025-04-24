import cv2
import socket
import struct


VIDEO_FILE = "Zorin_tests/testvideo.mp4"
IP = "192.168.186.41"
PORT = 5000
MAX_PACKET_SIZE = 65507


def main():

    cap = cv2.VideoCapture(VIDEO_FILE)
    if not cap.isOpened():
        print("Error: Could not open video file.")
        return

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    sequence_number = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            print("End of video file.")
            break

        ret, encoded_frame = cv2.imencode(".jpg", frame)
        if not ret:
            print("Error: Could not encode frame.")
            continue

        frame_data = encoded_frame.tobytes()

        for i in range(0, len(frame_data), MAX_PACKET_SIZE - 1):

            chunk = frame_data[i : i + (MAX_PACKET_SIZE - 1)]

            packet = struct.pack("B", sequence_number) + chunk

            sock.sendto(packet, (IP, PORT))

            sequence_number = (sequence_number + 1) % 256

    cap.release()
    sock.close()


if __name__ == "__main__":
    main()
