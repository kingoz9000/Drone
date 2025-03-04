 
import socket
import threading
 
class RelayClient:
    """RelayClient class to handle client requests"""
    def __init__(self):
        """Initialize the RelayClient object"""
        self.CLIENT_PORT: int = 5000
        self.CLIENT_ADDRESS: str = ""
        
    @staticmethod
    def startClientThread(func, *args) -> None:
        """General worker function to run a function in a thread""" 
        client_thread = threading.Thread(target=func, args=args, daemon=True)
        client_thread.start()
    
    def handle_client(self, client_data, client_address) -> None:
        """handle incoming client requests and send them to the modem"""
        try: 
            # seperate socket for each client
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
            client_socket.settimeout(30) # set timeout for socket to 30 seconds
            
            # send client data to modem
            client_socket.sendto(client_data, (self.MODEM_IP, self.MODEM_PORT))
            
            #recieve response from modem
            response, _ = client_socket.recvfrom(1024)

            #send response to client
            self.client_socket.sendto(response, client_address)
            
            client_socket.close()
            
        except socket.timeout:
            print("Socket timed out")
        except Exception as e:
            print(f"An error occured while handling client: {e}")