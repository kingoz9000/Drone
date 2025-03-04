from socket import *
from Pie_handler import PieHandler


class PieServer:
    def __init__(self):
        self.from_modem = PieHandler(False, ("127.0.0.1", 6969), ("192.168.10.1", 8889))
        self.from_drone = PieHandler(True, ("0.0.0.0", 8890), ("127.0.0.1", 9484))

        self.from_modem.start()
        self.from_drone.start()

        while True:
            asd = input()
            if asd == "exit":
                break


if __name__ == "__main__":
    PieServer()
