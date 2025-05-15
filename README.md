# Drone Communication Project P2 Aalborg University
This project is a second semester project on Aalborg University.
The goal of the project is to create a drone communication system using cellular networks.
The drone used is a Tello EDU drone in AP-mode with a device also connected to a cellular network.

# STUN integration
This project uses a custom STUN implementation with a connection establiser called `stun_server.py`.
The STUN server needs to have access to a public IP address and a port to listen on but the two clients can be used on any network that faciltates UDP communication.

## Hole punching or TURN
If the networks the clients are connected to uses non-EIM NAT type UDP hole punching will not work and TURN mode will be used instead.
The TURN function is also built into the connection establiser and will automatically switch if UDP hole punching fails.

# Controls
For this project the controller used is a Logitech ATK 3 and button mapping can be changed in by making a new `joystick` implementation.

# GUI
The GUI is built using customTKinter and is used to display the video stream from the drone and the connection status.
Also information from the Tello EDU state socket is shown.

# Tello drone
The tello drone uses H.264 video encoding and the video stream is decoded using an av container.
Also a buffer and costum reordering is used to ensure that the video stream is smooth and not choppy.

## Tello SDK 3.0 User Guide

https://dl.djicdn.com/downloads/RoboMaster+TT/Tello_SDK_3.0_User_Guide_en.pdf
