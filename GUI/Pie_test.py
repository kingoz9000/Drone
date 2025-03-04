from socket import *
import threading

BUFFER_SIZE = 4096

sender = socket(AF_INET, SOCK_DGRAM)


def sender_funtion():
    while True:
        msg = input()
        if msg == "exit":
            break
        s.sendto(bytes(msg, "utf-8"), ("127.0.0.1", 6969))


s = socket(AF_INET, SOCK_DGRAM)
s.bind(("127.0.0.1", 9484))


def reciever_funtion():
    global s
    while True:
        a, b = s.recvfrom(BUFFER_SIZE)
        print(a)
        print(b)


thread = threading.Thread(target=reciever_funtion, daemon=True)
thread.start()

sender_funtion()
