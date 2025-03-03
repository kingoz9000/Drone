#imports...
import socket

class ModemHandler:
    """Handles the modem connection and sends AT commands"""
    def __init__(self): 
        # sending AT commands to the modem
        self.AT_MODEM_PORT: int = 1 # port for AT commands
        self.AT_MODEM_ADRESS: str =  self.sendATCommand("AT+CGPADDR=1") # address for AT commands
        self.AT_COMMAND_SOCKET = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        
    def sendATCommand(self, command: str) -> None # send AT command to modem
        self.AT_COMMAND_SOCKET.sendto(command.encode('utf-8'), (self.AT_COMMAND_ADDRESS, self.AT_COMMAND_PORT)) # send AT command to modem
        response = self.AT_COMMAND_SOCKET.recv(1024) # recieve response from modem
        return response # return response from modem
        
    def setupConnection(self, apn = "internet"): # setup connection to modem
        # MUST be sent at least once everytime there is a firmware upgrade!
        self.sendATCommand(f'AT+CGDCONT=1,"IP","{apn}"') # start PDP context
        
        # (Optional, debug only, AT commands) Activate PDP context, retrieve IP address and test with ping
        self.sendATCommand("AT+CGACT=1,1") # Activate PDP context
        return self.sendATCommand("AT+CGPADDR=1") # Get IP address from modem
    
    def getSignalStrength(self): # (Optional, debug only, AT commands) Retrieve signal strength 
        return self.sendATCommand("AT+CSQ")
    
    def checkStatus(self):
        "check if modem is responsive, by sending AT command"
        response = self.sendATCommand("AT") 
        if response == "OK":
            return True
        else:   
            return False
    
if __name__ == "__main__":
    modem = ModemHandler()
    modem.setupConnection()
    modem.checkStatus()
    while True:
        pass