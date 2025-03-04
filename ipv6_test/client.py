import socket

sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM, 0)
sock.connect(address)
