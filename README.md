# Drone Project P2 Aalborg University

This project is about making a relay box for controlling a drone through UDP packages.
More information will follow

# Tello SDK 2.0 User Guide

https://dl-cdn.ryzerobotics.com/downloads/Tello/Tello%20SDK%202.0%20User%20Guide.pdf

# Overview

| **Control Station (GUI, Joystick)** | **Relay Box (Firetruck)** | **Tello Drone (UDP Control)** |
| ----------------------------------- | ------------------------- | ----------------------------- |
| PyQt / C++ Qt                       | WebSockets / gRPC         | Tello SDK (Python)            |
| Joystick Input                      | Wi-Fi Bridge              | Video Stream                  |

| **Component**                                           | **Best Language(s)**     | **Why?**                                              |
| ------------------------------------------------------- | ------------------------ | ----------------------------------------------------- |
| **1️⃣ Control Station (UI, Joystick, Command Center)**   | C++ (Qt), Python (PyQt)  | Fast, cross-platform UI with joystick support         |
| **2️⃣ Relay Box (Firetruck)**                            | Rust, Go, Python         | Lightweight and reliable for handling network traffic |
| **3️⃣ Tello Drone Control**                              | Python (djitellopy), C++ | Easiest way to control the drone via UDP              |
| **4️⃣ Communication Layer (Low-Latency Remote Control)** | WebRTC, gRPC, WebSockets | Ensures real-time commands & video streaming          |
