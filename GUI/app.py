from tkinter import Tk, Label, Text
from PIL import Image, ImageTk
from drone_communication import DroneCommunication
from joystick import JoystickHandler
from drone_video_feed import DroneVideoFeed
import threading
import time
import argparse
import cv2
from flask import Flask, Response, render_template


class TelloTkinterStream:
    def __init__(self, args):
        self.ARGS = args

        self.running = True

        # TODO: introduce stun peer

        drone_video_addr = ("0.0.0.0", 11111) if not args.stun else ("123", 123)
        drone_comm_addr = ("192.168.10.1", 8889) if not args.stun else ("123", 123)
        # Start video stream and communication with the drone
        self.video_stream: DroneVideoFeed = DroneVideoFeed(drone_video_addr)
        self.drone_communication: DroneCommunication = DroneCommunication(
            drone_comm_addr
        )

        # Initialize joystick
        self.joystick = JoystickHandler()
        if self.joystick.joystick:
            self.run_in_thread(self.joystick.start_reading)

        # Initialize drone battery variable
        self.drone_battery = None

        # Main thread
        self.run_in_thread(self.main)

        self.app = Flask(__name__)
        self.setup_routes()

        self.latest_frame = None  # Store last frame
        self.run_in_thread(self.process_video_stream)

        self.app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)

    def setup_routes(self):
        """Define Flask routes dynamically"""
        self.app.add_url_rule("/", "index", self.index)
        self.app.add_url_rule("/video_feed", "video_feed", self.video_feed)

    def index(self):
        """Render external HTML file"""
        return render_template("index.html")  

    def video_feed(self):
        '''Route for streaming video in the browser.'''
        return Response(self.generate_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")
    
    def process_video_stream(self):
        """Continuously processes and stores the latest frame in a thread."""
        while self.running:
            frame = self.video_stream.get_frame()

            if frame is not None:
                frame = cv2.resize(frame, (640, 480))  # Resize for speed
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Fix blue tint
                self.latest_frame = frame  # Store latest frame for streaming


    def generate_frames(self):
        """Yields the most recent frame when requested."""
        while self.running:
            if self.latest_frame is not None:
                _, buffer = cv2.imencode(".jpg", self.latest_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
                frame_bytes = buffer.tobytes()

                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
                )



    def control_drone(self):
        if not self.joystick.joystick:
            return

        # Weights and other values
        deadzone = 5

        # Values from joystick
        x, y, z, buttons = self.joystick.get_values()

        weight = (-z + 1) * 50

        for_backward = x * weight
        for_backward = 0 if -deadzone < for_backward < deadzone else for_backward

        left_right = y * -1 * weight
        left_right = 0 if -deadzone < left_right < deadzone else left_right

        up_down = 0
        yaw = 0

        # Button actions
        for button_key, button_value in buttons.items():
            if not button_value:
                continue
            match button_key:
                case 1:
                    print("Bang!")
                case 2:
                    up_down -= weight
                case 3:
                    up_down += weight
                case 4:
                    yaw -= weight
                case 5:
                    yaw += weight
                case 6:
                    self.drone_communication.send_command("reboot")
                case 8:
                    self.drone_communication.send_command("takeoff")
                case 9:
                    self.drone_communication.send_command("land")
                case 10:
                    self.drone_communication.send_command(
                        "battery?", take_response=True
                    )
                case _:
                    self.drone_communication.send_command("emergency")

        command = f"rc {for_backward:.2f} {left_right:.2f} {up_down} {yaw}"
        self.drone_communication.send_command(command, False)

    def get_ping(self):
        if self.ARGS.noping:
            return

        start_time = time.perf_counter_ns()
        self.drone_battery = self.drone_communication.send_command(
            "battery?", take_response=True
        )
        end_time = time.perf_counter_ns()

        ping = (end_time - start_time) // 1000000

        print(f"Ping for communication: {ping} ms")

        self.drone_stats.delete("1.0", "end")
        self.drone_stats.insert(
            "1.0", f"Battery: {self.drone_battery.strip()}% \nPing: {ping} ms"
        )

    def main(self):
        while self.running:
            self.control_drone()

            self.get_ping()

            time.sleep(0.05)

    def cleanup(self) -> None:
        """Safely clean up resources and close the Tkinter window."""
        print("Shutting down...")

        self.running = False
        self.video_stream.stop()
        self.drone_communication.stop()


    @staticmethod
    def run_in_thread(func, *args) -> threading.Thread:
        """General worker function to run a function in a thread"""
        thread = threading.Thread(target=func, args=args, daemon=True)
        thread.start()
        return thread


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-s", "--stun", help="Use stun to remote control", action="store_true"
    )
    parser.add_argument("-np", "--noping", help="Disable ping", action="store_true")
    args = parser.parse_args()

    TelloTkinterStream(args)
