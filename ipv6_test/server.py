import socket

sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM, 0)
sock.bind("", 4565, 0, 0)
sock.listen(1)
try:
    while True:
        c, a = sock.accept()
        response = c.recv(1024)
        c.send(bytes("Not a fish", "utf-8"))
        c.close()


except:
    sock.close()
