import socket

sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM, 0)
sock.connect(("fd9f:87a9:7276::282/128", 4565, 0, 0))

sock.send(bytes("Fish", "utf-8"))
data = sock.recv(1024)
print(data.decode("utf-8"))
sock.close()
