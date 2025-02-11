# Drone Project P2 Aalborg University
This project is about making a relay box for controlling a drone through UDP packages.
More information will follow

# djitellopy repository
https://github.com/damiafuentes/DJITelloPy

# Tello SDK 2.0 User Guide
https://dl-cdn.ryzerobotics.com/downloads/Tello/Tello%20SDK%202.0%20User%20Guide.pdf

# Tello SDK 2.0 Interface Description
https://dl-cdn.ryzerobotics.com/downloads/Tello/Tello%20SDK%202.0%20Interface%20Description.pdf

# Tello SDK 2.0 Communication Protocol
https://dl-cdn.ryzerobotics.com/downloads/Tello/Tello%20SDK%202.0%20Communication%20Protocol.pdf

# Tello SDK 2.0 Sample `Python` Code   

```python 
import socket
import threading
import time 

# IP and port of Tello
tello_address = ('192.168.10.1', 8889)

# IP and port of local computer
local_address = ('', 9000)

# Create a UDP connection that we'll send the command to
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Bind to the local address and port
sock.bind(local_address)

# Send the message to Tello and allow for a delay in seconds
def send(message):
  try:
    sock.sendto(message.encode(), tello_address)
    print("Sending message: " + message)
  except Exception as e:
    print("Error sending: " + str(e))

# Receive the message from Tello
def receive():
  while True:
    try:
      response, ip_address = sock.recvfrom(128)
      print("Received message: " + response.decode(encoding='utf-8'))
    except Exception as e:
      sock.close()
      print("Error receiving: " + str(e))
      break

      # Create and start a listening thread that runs in the background
receiveThread = threading.Thread(target=receive)
receiveThread.daemon = True
receiveThread.start()

# Tell the user what to do  
print("Type in a Tello SDK command and press the enter key. Enter 'quit' to exit this program.")

# Loop infinitely waiting for commands or until the user types quit
while True:
  try:
    message = input('')
    if 'quit' in message:
      print("Program exited \r\n")
      sock.close()
      break
    send(message)
  except KeyboardInterrupt as e:
    sock.close()
    break
```



# Overview
| **Control Station (GUI, Joystick)** | **Relay Box (Firetruck)** | **Tello Drone (UDP Control)** |
|-------------------------------------|---------------------------|------------------------------|
| PyQt / C++ Qt                       | WebSockets / gRPC         | Tello SDK (Python)           |
| Joystick Input                      | Wi-Fi Bridge              | Video Stream                 |

| **Component** | **Best Language(s)** | **Why?** |
|--------------|----------------------|----------|
| **1️⃣ Control Station (UI, Joystick, Command Center)** | C++ (Qt), Python (PyQt) | Fast, cross-platform UI with joystick support |
| **2️⃣ Relay Box (Firetruck)** | Rust, Go, Python | Lightweight and reliable for handling network traffic |
| **3️⃣ Tello Drone Control** | Python (djitellopy), C++ | Easiest way to control the drone via UDP |
| **4️⃣ Communication Layer (Low-Latency Remote Control)** | WebRTC, gRPC, WebSockets | Ensures real-time commands & video streaming |

