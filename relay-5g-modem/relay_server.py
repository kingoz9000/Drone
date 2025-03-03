import socket
import threading

from modem_handler import ModemHandler

class RelayServer:
    def __init__(self):
        """Initialize the RelayServer object"""
        self.RELAY_PORT: int = 1
        self.RELAY_ADDRESS: str = ""
        
        self.MODEM_IP: str = ModemHandler.AT_MODEM_ADDRESS
        self.MODEM_PORT: int = ModemHandler.AT_MODEM_PORT
        
         # create udp socket for relay server
        self.RELAY_SOCKET = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.RELAY_SOCKET.bind((self.RELAY_ADDRESS, self.RELAY_PORT)) 
        self.RELAY_SOCKET.settimeout(30) # set timeout for socket to 30 seconds
    
    def listen_for_clients(self) -> None:
        """Listen for incoming client requests"""
        while True:
            try:
                # retrieve client data and address
                client_data, client_address = self.RELAY_SOCKET.recvfrom(1024) 
                # handle client requests in a new thread
                self.startClientThread(self.handle_client, client_data, client_address)
            except KeyboardInterrupt:
                print("Shutting down relay server")
                break
            except Exception as e:
                print(f"An error occured while listening for clients: {e}")
    
    @staticmethod
    def startClientThread(func, *args) -> None:
        """General worker function to run a function in a thread""" 
        client_thread = threading.Thread(target=func, args=args, daemon=True)
        client_thread.start()
    
    def handle_client(self, client_data, client_address) -> None:
        """handle incoming client requests and send them to the modem"""
        try: 
            # send client data to modem
            self.RELAY_SOCKET.sendto(client_data, (self.MODEM_IP, self.MODEM_PORT))
            
            #recieve response from modem
            response, _ = self.RELAY_SOCKET.recvfrom(1024)

            #send response to client
            self.RELAY_SOCKET.sendto(response, client_address)
            
            self.RELAY_SOCKET.close()
            
        except socket.timeout:
            print("Socket timed out")
        except Exception as e:
            print(f"An error occured while handling client: {e}")
            
if __name__ == "__main__":
    relay_server = RelayServer()
    relay_server.listen_for_clients()
    while True:
        pass
    
        
        
        
        
        
        
       
        
        
        
        
        