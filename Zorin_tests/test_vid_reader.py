import socket
import struct

# Configuration
LOOPBACK_IP = "127.0.0.1"
PORT = 5000
MAX_PACKET_SIZE = 65507  # Maximum UDP packet size

def main():
    # Create a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((LOOPBACK_IP, PORT))

    print(f"Listening for video stream on {LOOPBACK_IP}:{PORT}...")

    last_sequence_number = None

    while True:
        # Receive a packet
        packet, addr = sock.recvfrom(MAX_PACKET_SIZE)

        # Extract the sequence number (1 byte)
        sequence_number = struct.unpack("B", packet[:1])[0]

        # Print the sequence number
        print(f"Received packet with sequence number: {sequence_number}")

        # Check for packet reordering
        if last_sequence_number is not None:
            expected_sequence_number = (last_sequence_number + 1) % 256
            if sequence_number != expected_sequence_number:
                print(f"Warning: Packet reordering detected! Expected {expected_sequence_number}, got {sequence_number}")

        # Update the last sequence number
        last_sequence_number = sequence_number

if __name__ == "__main__":
    main()