 
import socket
import threading

from modem_handler import ModemHandler
 
class RelayClient:
    """RelayClient class to handle client requests"""
    def __init__(self, client_data, client_address):
        """Initialize the RelayClient object"""
        self.client_data = client_data
        self.client_address = client_address
        self.MODEM_IP: str = ModemHandler.AT_MODEM_ADDRESS
        self.MODEM_PORT: int = ModemHandler.AT_MODEM_PORT
        
    @staticmethod
    def startClientThread(func, *args) -> None:
        """General worker function to run a function in a thread""" 
        client_thread = threading.Thread(target=func, args=args, daemon=True)
        client_thread.start()
    
    def handle_client(self, client_data, client_address) -> None:
        """handle incoming client requests and send them to the modem"""
        try: 
            # separate socket for each client
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
            client_socket.settimeout(30) # set timeout for socket to 30 seconds
            
            # send client data to modem
            client_socket.sendto(client_data, (self.MODEM_IP, self.MODEM_PORT))
            
            #recieve response from modem
            response, _ = client_socket.recvfrom(1024)

            #send response to client
            client_socket.sendto(response, client_address)
            
            client_socket.close()
            
        except socket.timeout:
            print("Socket timed out")
        except Exception as e:
            print(f"An error occured while handling client: {e}")