import socket

SERVER_IP = "0.0.0.0"  # Listen on all interfaces
SERVER_PORT = 12345

clients = {}  # Store (client_id: (ip, port))

server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind((SERVER_IP, SERVER_PORT))

print(f"Server listening on {SERVER_IP}:{SERVER_PORT}")

while True:
    data, addr = server_socket.recvfrom(1024)
    message = data.decode().strip()

    if message.startswith("REGISTER"):
        client_id = len(clients) + 1
        clients[client_id] = addr
        server_socket.sendto(f"REGISTERED {client_id}".encode(), addr)
        print(f"Client {client_id} registered from {addr}")

    elif message.startswith("REQUEST"):
        _, target_id = message.split()
        target_id = int(target_id)

        if target_id in clients:
            target_addr = clients[target_id]
            requester_id = [k for k, v in clients.items() if v == addr][0]

            # Send both clients each other's public IP and port
            server_socket.sendto(f"PEER {target_addr[0]} {target_addr[1]}".encode(), addr)
            server_socket.sendto(f"PEER {addr[0]} {addr[1]}".encode(), target_addr)
            print(f"Exchanged details between Client {requester_id} and Client {target_id}")

        else:
            server_socket.sendto("NOT_FOUND".encode(), addr)

