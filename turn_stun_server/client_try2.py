import socket
import threading
import time

SERVER_IP = "130.225.37.157"  # Change this to your real server's IP
SERVER_PORT = 12345

def listen(sock):
    while True:
        global peer_port
        global peer_ip
        data, addr = sock.recvfrom(1024)
        message = data.decode()

        if message.startswith("PEER"):
            _, peer_ip, peer_port = message.split()
            peer_port = int(peer_port)
            print(f"🔗 Connecting to peer at {peer_ip}:{peer_port}")

            # Send a "hole punching" packet to open NAT
            for _ in range(10):  # Send multiple in case some are dropped
                sock.sendto(b"HOLE_PUNCH", (peer_ip, peer_port))
                time.sleep(1)

            print("✅ Hole punching complete. Start chatting!")

        else:
            print(f"📩 Received: {message}")

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("", 0))  # Bind to an ephemeral port

    # Register with server
    sock.sendto(b"REGISTER", (SERVER_IP, SERVER_PORT))
    response, _ = sock.recvfrom(1024)
    client_id = response.decode().split()[1]
    print(f"✅ Registered as Client {client_id}")

    # Start listening for messages
    threading.Thread(target=listen, args=(sock,), daemon=True).start()

    # Request a peer
    peer_id = input("Enter peer ID: ")
    sock.sendto(f"REQUEST {peer_id}".encode(), (SERVER_IP, SERVER_PORT))

    # Chat loop
    while True:
        msg = input("You: ")
        sock.sendto(msg.encode(), (peer_ip, peer_port))

if __name__ == "__main__":
    main()

