import socket

SERVER_IP = "0.0.0.0"  # Listen on all interfaces
SERVER_PORT = 12345

clients = {}  # Store (client_id: [(ip, port), target_id])

server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind((SERVER_IP, SERVER_PORT))

print(f"Server listening on {SERVER_IP}:{SERVER_PORT}")


def get_client_id(addr):
    for k, v in clients.items():
        if v[0] == addr:
            return k
    return None

while True:
    data, addr = server_socket.recvfrom(1024)
    message = data.decode().strip()

    if message.startswith("REGISTER"):
        client_id = len(clients) + 1
        clients[client_id] = [addr, None]
        server_socket.sendto(f"REGISTERED {client_id}".encode(), addr)
        print(f"Client {client_id} registered from {addr}")
        
    elif message.startswith("REQUEST"):
        _, target_id = message.split()
        target_id = int(target_id)
        current_client_id = get_client_id(addr)

        if target_id in clients:
            clients[current_client_id][1] = target_id
            target_addr = clients[target_id][0]

            if clients[target_id][1] == current_client_id:
                # Send both clients each other's public IP and port
                server_socket.sendto(f"PEER {target_addr[0]} {target_addr[1]}".encode(), addr)
                server_socket.sendto(f"PEER {addr[0]} {addr[1]}".encode(), target_addr)
                print(f"Exchanged details between Client {current_client_id} and Client {target_id}")
            else:
                print(f"Client {current_client_id} requested Client {target_id}, but target not set reciprocally.")
        else:
            server_socket.sendto("NOT_FOUND".encode(), addr)

