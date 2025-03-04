import socket

sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM, 0)
sock.connect("2a02:aa7:4643:7046:e0fd:e0ff:fe49:1cdb", 4565, 0, 0)

sock.send(bytes("Fish", "utf-8"))
data = sock.recv(1024)
print(data.decode("utf-8"))
sock.close()
