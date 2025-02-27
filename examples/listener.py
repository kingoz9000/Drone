import socket

def main():
    # Create a socket object
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Allow reusing the port if the server is restarted quickly
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Bind to all available interfaces on the specified port
    host = "0.0.0.0"  # This allows the server to accept connections from any IP
    port = 51843
    server_socket.bind((host, port))

    # Listen for incoming connections
    server_socket.listen(5)
    print(f"Server listening on {host}:{port}")

    while True:
        # Accept a new connection
        client_socket, addr = server_socket.accept()
        print(f"Connection established with {addr}")

        try:
            while True:
                # Receive data from client
                data = client_socket.recv(1024)
                if not data:
                    print("Client disconnected")
                    break
                print(f"Received: {data.decode()}")
                
                # Echo the received message back to the client
                client_socket.send(data)
        except Exception as e:
            print("Connection error:", e)
        finally:
            client_socket.close()
            print("Client socket closed")

if __name__ == "__main__":
    main()

