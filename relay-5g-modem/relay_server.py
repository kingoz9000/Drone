import socket
import threading

class RelayServer:
    def __init__(self):
        """Initialize the RelayServer object"""
        self.RELAY_PORT: int = 8888
        self.RELAY_ADDRESS: str = ""
        self.MODEM_IP: str = "" 
        self.MODEM_PORT: int = 1
        
         # create udp socket for relay server
        self.RELAY_SOCKET = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.RELAY_SOCKET.bind((self.RELAY_ADDRESS, self.RELAY_PORT)) 
        self.RELAY_SOCKET.settimeout(5) # set timeout for socket to 5 seconds
    
    def listen_for_clients(self) -> None:
        """Listen for incoming client requests"""
        while True:
            try:
                # retrieve client data and address
                client_data, client_adress = self.RELAY_SOCKET.recvfrom(1024) 
                # handle client requests in a new thread
                self.startClientThread(client_data, client_adress)
            except KeyboardInterrupt:
                print("Shutting down relay server")
                break
            except Exception as e:
                print(f"An error occured while listening for clients: {e}")
    
    @staticmethod
    def startClientThread(self, *args) -> None:
        """General worker function to run a function in a thread"""
        client_thread = threading.Thread(target=self.handle_client, args=args, daemon=True)
        client_thread.start()
    
    def handle_client(self, client_data, client_adress) -> None:
        """handle incoming client requests and send them to the modem"""
        try: 
            # send client data to modem
            self.RELAY_SOCKET.sendto(client_data, (self.MODEM_IP, self.MODEM_PORT))
            
            #recieve response from modem
            response, _ = self.RELAY_SOCKET.recvfrom(1024)

            #send response to client
            self.RELAY_SOCKET.sendto(response, client_adress)
            
        except socket.timeout:
            print("Socket timed out")
        except Exception as e:
            print(f"An error occured while handling client: {e}")
            
if __name__ == "__main__":
    relay_server = RelayServer()
    relay_server.listen_for_clients()
    while True:
        pass
    
        
        
        
        
        
        
       
        
        
        
        
        