from socket import *
from time import sleep

datalist = []

with open("asd", "rb") as file:
    for line in file.readlines():
        line = line[2:-2]
        newline = line.decode("unicode-escape").encode("ISO-8859-1")
        datalist.append(newline)

sock = socket(AF_INET, SOCK_DGRAM)
sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

while True:
    for frame in datalist:
        sleep(1 / 30)
        sock.sendto(frame, ("127.0.0.1", 24523))
