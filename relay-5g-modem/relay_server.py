import socket
import threading

from modem_handler import ModemHandler
from relay_client import RelayClient

class RelayServer:
    def __init__(self):
        """Initialize the RelayServer object"""
        self.RELAY_PORT: int = 5000
        self.RELAY_ADDRESS: str = "0.0.0.0"
        
         # create udp socket for relay server
        self.RELAY_SOCKET = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.RELAY_SOCKET.bind((self.RELAY_ADDRESS, self.RELAY_PORT)) 
        self.RELAY_SOCKET.settimeout(30) # set timeout for socket to 30 seconds
    
    def listen_for_clients(self) -> None:
        """Listen for incoming client requests"""
        while True:
            try:
                # retrieve client data and address
                RelayClient.client_data, RelayClient.client_address = self.RELAY_SOCKET.recvfrom(1024)
                # handle client requests in a new thread
                RelayClient.startClientThread(RelayClient.handle_client, RelayClient.client_data, RelayClient.client_address)
            except KeyboardInterrupt:
                print("Shutting down relay server")
                break
            except Exception as e:
                print(f"An error occured while listening for clients: {e}")
      
if __name__ == "__main__":
    relay_server = RelayServer()
    relay_server.listen_for_clients()
    while True:
        pass
    