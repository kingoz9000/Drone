import threading
from socket import *


class PieHandler:
    def __init__(self, is_modem_sender: bool, recv_address, send_address):
        send_adapter = "wlp2s0\0"
        recieve_adapter = "wlp2s0\0"

        # if is_modem:
        #    send_adapter = "cdc-wdm0"
        # else:
        #    recieve_adapter = "cdc-wdm0"

        self.send_sock: socket = socket(AF_INET, SOCK_DGRAM)
        self.send_sock.setsockopt(SOL_SOCKET, 25, send_adapter.encode("utf-8"))

        self.recieve_sock: socket = socket(AF_INET, SOCK_DGRAM)
        self.recieve_sock.setsockopt(SOL_SOCKET, 25, recieve_adapter.encode("utf-8"))
        self.recieve_sock.bind(recv_address)

        self.send_address = send_address
        self.BUFFER_SIZE = 4096

        self.response = None

    def recieve(self):
        while True:
            response, _addr = self.recieve_sock.recvfrom(self.BUFFER_SIZE)

            self.response = response

    def sender(self):
        while True:
            if self.response == None:
                continue
            self.send_sock.sendto(self.response, self.send_address)
            self.response = None

    def start(self):
        thread_recv = threading.Thread(target=self.recieve, daemon=True)
        thread_recv.start()

        thread_send = threading.Thread(target=self.sender, daemon=True)
        thread_send.start()
