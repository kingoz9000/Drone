#imports...
import socket

class ModemHandler:
    """Handles the modem connection and sends AT commands"""
    def __init__(self): # sending AT commands to the modem
        self.AT_COMMAND_PORT = ""
        self.AT_COMMAND_ADDRESS = ""
        self.AT_COMMAND_SOCKET = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
    def sendATCommand(self, command ) -> str: # send AT command to modem
        self.AT_COMMAND_SOCKET.sendto("AT".encode('utf-8'), (self.AT_COMMAND_ADDRESS, self.AT_COMMAND_PORT)) # send AT command to modem
        response = self.AT_COMMAND_SOCKET.recv(1024) # recieve response from modem
        return response # return response from modem
        
    def setupConnection(self, apn = "internet"): # setup connection to modem
        # MUST be sent at least once everytime there is a firmware upgrade!
        self.sendATCommand("AT+CGDCONT=1","IP","{apn}") # send AT command to modem
        
        # (Optional, debug only, AT commands) Activate PDP context, retrieve IP address and test with ping
        self.sendATCommand("AT+CGACT=1,1") # send AT command to modem
        return self.sendATCommand("AT+CGPADDR=1") # Get IP address from modem
    
        # (Optional, debug only, AT commands) Retrieve signal strength      
        # self.sendATCommand("AT+CSQ") # send AT command to modem
        
    
    
if __name__ == "__main__":
    modem = ModemHandler()
    modem.setupConnection()
    while True:
        pass