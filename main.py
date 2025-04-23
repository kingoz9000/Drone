import argparse, threading, time
from tkinter import Canvas, Text, Tk
from collections import deque

from joystick.button_mapping import ButtonMap
from GUI.drone_communication import DroneCommunication
from GUI.drone_video_feed import DroneVideoFeed
from PIL import Image, ImageTk
from stun import ControlStunClient


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
            self.peer_addr = self.get_peer_address()
            time.sleep(5)
            drone_video_addr = ("0.0.0.0", 27463)
            self.send_command = self.stun_handler.send_command_to_relay
        else:
            drone_video_addr = ("0.0.0.0", 11111)
            drone_comm_addr = ("192.168.10.1", 8889)
            self.drone_communication = DroneCommunication(drone_comm_addr, 9000)
            self.send_command = self.drone_communication.send_command

        # Start video stream and communication with the drone
        self.video_stream = DroneVideoFeed(drone_video_addr)

        self.connect_to_drone()
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

    def get_peer_address(self) -> tuple:
        self.stun_handler = ControlStunClient()
        self.stun_handler.main()
        for _ in range(10):
            if self.stun_handler.hole_punched:
                print("Peer to Peer connection established")
                return self.stun_handler.get_peer_addr()
            time.sleep(1)

        raise Exception("Failed to establish peer-to-peer connection")

    def connect_to_drone(self) -> None:
        self.send_command("command")
        self.send_command("streamon")

    def update_video_frame(self) -> None:
        """Update the video frame in the Tkinter window."""
        frame = self.video_stream.get_frame()
        if frame is not None:
            try:
                img = Image.fromarray(frame)

                # Maybe remove this
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

        if not button_map.joystick_handler.joystick:
            return

        while True:
            commands = button_map.get_joystick_values()

            for command in commands:
                self.send_command(command, print_command=False)

            time.sleep(0.1)

    def get_ping(self) -> None:
        if self.ARGS.noping:
            return

        ping_data = deque(maxlen=10)
        prev_length = 0

        while True:
            start_time = time.perf_counter_ns()
            self.drone_battery = self.send_command("battery?", False, True)

            if self.ARGS.stun:
                while self.stun_handler.response.qsize() == prev_length:
                    time.sleep(0.01)
                self.drone_battery = self.stun_handler.response.get().decode()
                prev_length = self.stun_handler.response.qsize()

            end_time = time.perf_counter_ns()
            ping_ns = end_time - start_time
            ping_data.append(ping_ns)

            avg_ping_ms = sum(ping_data) // len(ping_data) // 1_000_000

            self.drone_stats.delete("1.0", "end")

            if type(self.drone_battery) is str:
                self.drone_stats.insert(
                    "1.0",
                    f"Battery: {self.drone_battery.strip()}% \nPing: {avg_ping_ms:03d} ms",
                )
                time.sleep(0.2)
            else:
                self.drone_stats.insert(
                    "1.0", f"Bad connection! Lost packages\nPing: {avg_ping_ms:03d}+ ms"
                )

    def cleanup(self) -> None:
        """Safely clean up resources and close the Tkinter window."""
        print("Shutting down...")

        self.send_command("streamoff")

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
