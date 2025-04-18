from tkinter import Tk, Canvas, Text
from PIL import Image, ImageTk
from drone_communication import DroneCommunication
from drone_video_feed import DroneVideoFeed
from stun.stun_client import StunClient
from button_mapping import ButtonMap
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
        self.video_canvas = Canvas(self.root, width=960, height=720)
        self.video_canvas.pack()

        # Bind cleanup to window close and q key
        self.root.protocol("WM_DELETE_WINDOW", self.cleanup)
        self.root.bind("q", lambda e: self.cleanup())

        self.print_to_image("1.0", "Battery: xx% \nPing xx ms")

        if args.stun:
            self.peer_addr = self.stun_connect()
            time.sleep(5)
            self.start_stun()
        else:
            self.peer_addr = None

        drone_video_addr = ("0.0.0.0", 11111) if not args.stun else ("0.0.0.0", 27463)
        drone_comm_addr = ("192.168.10.1", 8889) if not args.stun else self.peer_addr

        # Start video stream and communication with the drone
        self.drone_communication = DroneCommunication(drone_comm_addr, 9000)
        self.video_stream = DroneVideoFeed(drone_video_addr)

        # Initialize drone battery variable
        self.drone_battery = None

        # Threads for joystick controls and pinging
        self.run_in_thread(self.control_drone)
        self.run_in_thread(self.get_ping)

        # Start video update loop
        self.update_video_frame()

        # Start Tkinter event loop
        self.root.mainloop()

    def print_to_image(self, pos, text) -> None:
        self.drone_stats = Text(self.root, height=2, width=30)
        self.drone_stats.pack()
        self.drone_stats.insert(pos, text)
        self.drone_stats.config()

    def stun_connect(self) -> tuple:
        self.stun_handler = StunClient()
        self.stun_handler.main()
        for _ in range(10):
            if self.stun_handler.hole_punched:
                print("Peer to Peer connection established")
                return self.stun_handler.get_peer_addr()
            time.sleep(1)

    def monitor_connection(self) -> None:
        while True:
            # update ui if connection is lost
            if not self.stun_handler.hole_punched:
                self.drone_stats.insert("1.0", "Connection lost")
                break
            time.sleep(2)

    def start_stun(self) -> None:
        self.stun_handler.send_command("command")
        self.stun_handler.send_command("streamon")

    def update_video_frame(self) -> None:
        """Update the video frame in the Tkinter window."""
        frame = self.video_stream.get_frame()
        if frame is not None:
            try:
                img = Image.fromarray(frame)
                img = img.resize((960, 720), Image.Resampling.LANCZOS)

                imgtk = ImageTk.PhotoImage(image=img)

                # Update the label using the main thread
                self.root.after(0, self.update_canvas, imgtk)

            except Exception as e:
                print(f"Error updating video frame: {e}")

        self.root.after(10, self.update_video_frame)

    def update_canvas(self, imgtk):
        """Update Canvas with the new video frame."""
        self.video_canvas.create_image(0, 0, anchor="nw", image=imgtk)
        self.video_canvas.imgtk = imgtk  # Prevent garbage collection

    def control_drone(self) -> None:
        button_map = ButtonMap()

        if not button_map.joystick.joystick:
            return

        command_send = None
        if self.ARGS.stun:
            command_send = self.stun_handler.send_command
        else:
            command_send = self.drone_communication.send_command

        while True:
            commands = button_map.get_joystick_values()

            for command in commands:
                command_send(command, print_command=False)

            time.sleep(0.1)

    # TODO: fix this function
    def get_ping(self) -> None:
        ping_data: list[int] = [0 for _ in range(10)]
        while True:
            if self.ARGS.noping:
                return

            for i in range(10):
                start_time = time.perf_counter_ns()
                self.drone_battery = self.drone_communication.send_command(
                    "battery?", False, True
                )
                end_time = time.perf_counter_ns()
                ping_data[i] = end_time - start_time

            ping = sum(ping_data) // 10000000

            if type(self.drone_battery) is str:
                self.drone_stats.delete("1.0", "end")
                self.drone_stats.insert(
                    "1.0",
                    f"Battery: {self.drone_battery.strip()}% \nPing: {ping:03d} ms",
                )
            else:
                self.drone_stats.delete("1.0", "end")
                self.drone_stats.insert(
                    "1.0", f"Bad connection! Lost packages\nPing: {ping:03d}+ ms"
                )

            if ping < 1000:
                time.sleep(1 - ping / 1024)

    def cleanup(self) -> None:
        """Safely clean up resources and close the Tkinter window."""
        print("Shutting down...")

        if self.ARGS.stun:
            self.stun_handler.send_command("streamoff")
        else:
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
