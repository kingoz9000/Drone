import socket
import time

def main():
    # Create a socket object
    s = socket.socket()
    print("Socket created")

    # Define the port and server IP
    port = 51843
    ip = "130.225.196.7"

    try:
        s.connect((ip, port))
        print(f"Connected to {ip}:{port}")
    except Exception as e:
        print("Connection Error:", e)
        return

    try:
        while True:
            # Send a packet with "hej"
            message = "hej"
            s.send(message.encode())
            print(f"Sent: {message}")
            time.sleep(1)  # Prevents flooding the server
    except Exception as e:
        print("Error sending data:", e)
    finally:
        s.close()
        print("Socket closed")

if __name__ == "__main__":
    main()

