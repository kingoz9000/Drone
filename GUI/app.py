from tkinter import Tk, Label, Text
from PIL import Image, ImageTk
from drone_communication import DroneCommunication
from joystick import JoystickHandler
from drone_video_feed import DroneVideoFeed
from stun.stun_client import StunClient
import threading
import time
import argparse


class TelloTkinterStream:
    def __init__(self, args):
        self.ARGS = args

        # Initialize Tkinter window and Tello video stream.
        self.root: Tk = Tk()
        self.root.title("Tello Video Stream")
        self.root.geometry("1280x920")

        # Create a label to display the video
        self.video_label: Label = Label(self.root)
        self.video_label.pack()

        self.drone_stats = Text(self.root, height=2, width=30)
        self.drone_stats.pack()
        self.drone_stats.insert("1.0", f"Battery: xx% \nPing xx ms")
        self.drone_stats.config(state="disabled")

        self.running = True

        # TODO: introduce stun peer

        peer_addr = None
        if args.stun:
            self.stun_handler = StunClient()
            self.stun_handler.main()
            for _ in range(10):
                if self.stun_handler.hole_punched:
                    peer_addr = self.stun_handler.get_peer_addr()
                    print("Peer to Peer connection established")
                    break
                time.sleep(1)

            if peer_addr is None:
                print("Failed to connect")
                return
        time.sleep(5)
        self.stun_handler.send_command("command")
        self.stun_handler.send_command("streamon")

        drone_video_addr = ("0.0.0.0", 11111) if not args.stun else peer_addr
        drone_comm_addr = ("192.168.10.1", 8889) if not args.stun else peer_addr
        # Start video stream and communication with the drone
        self.drone_communication: DroneCommunication = DroneCommunication(
            drone_comm_addr
        )
        self.video_stream: DroneVideoFeed = DroneVideoFeed(drone_video_addr)

        # Initialize joystick
        self.joystick = JoystickHandler()
        if self.joystick.joystick:
            self.run_in_thread(self.joystick.start_reading)

        # Initialize drone battery variable
        self.drone_battery = None

        # Main thread
        self.run_in_thread(self.main)

        # Start video update loop
        self.update_video_frame()

        # Bind cleanup to window close and q key
        self.root.protocol("WM_DELETE_WINDOW", self.cleanup)
        self.root.bind("q", lambda e: self.cleanup())

        # Start Tkinter event loop
        self.root.mainloop()

    def update_video_frame(self) -> None:
        """Update the video frame in the Tkinter window."""
        frame = self.video_stream.get_frame()
        if frame is not None:
            try:
                img = Image.fromarray(frame)
                imgtk = ImageTk.PhotoImage(image=img)

                # Update the label using the main thread
                self.root.after(0, self.update_label, imgtk)

            except Exception as e:
                print(f"Error updating video frame: {e}")

        self.root.after(10, self.update_video_frame)

    def update_label(self, imgtk):
        """Safely update Tkinter Label from a different thread"""
        self.video_label.imgtk = imgtk
        self.video_label.config(image=imgtk)

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

        command_send = None
        if self.ARGS.stun:
            command_send = self.stun_handler.send_command
        else:
            command_send = self.drone_communication.send_command
        # Button actions
        for button_key, button_value in buttons.items():
            if not button_value:
                continue
            match button_key:
                case 1:
                    self.drone_communication.send_command("flip f")
                case 2:
                    up_down -= weight
                case 3:
                    up_down += weight
                case 4:
                    yaw -= weight
                case 5:
                    yaw += weight
                case 6:
                    command_send("reboot")
                case 8:
                    command_send("takeoff")
                case 9:
                    command_send("land")
                case 10:
                    command_send("battery?", take_response=True)
                case _:
                    self.drone_communication.send_command("emergency")

        command = f"rc {for_backward:.2f} {left_right:.2f} {up_down} {yaw}"
        command_send(command, True)

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

        self.root.quit()
        self.root.destroy()

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
