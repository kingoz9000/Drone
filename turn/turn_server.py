import socket
import threading
import time

class TURNServer:
    def __init__(self):
        self.TURN_SERVER_IP = "0.0.0.0"
        self.TURN_SERVER_PORT = 12345
        self.turn_clients = {}
        self.turn_clients_lock = threading.Lock()
        self.turn_server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.turn_server_socket.bind((self.TURN_SERVER_IP, self.TURN_SERVER_PORT))
        
        