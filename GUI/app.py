from tkinter import Tk, Label, Text
from PIL import Image, ImageTk
from drone_communication import DroneCommunication
from joystick import JoystickHandler
from drone_video_feed import DroneVideoFeed
import threading
import time


class TelloTkinterStream:
    def __init__(self):
        """Initialize Tkinter window and Tello video stream."""
        self.root: Tk = Tk()
        self.root.title("Tello Video Stream")
        self.root.geometry("1280x920")

        # Create a label to display the video
        self.video_label: Label = Label(self.root)
        self.video_label.pack()

        self.drone_stats = Text(self.root, height=2, width=30)
        self.drone_stats.pack()
        self.drone_stats.insert("1.0", f"Battery: xx% \nPing xx ms")

        self.running = True

        # Start video stream and communication with the drone
        self.video_stream: DroneVideoFeed = DroneVideoFeed()
        self.drone_communication: DroneCommunication = DroneCommunication()

        # Initialize joystick
        self.joystick = JoystickHandler()
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
                    self.drone_communication.send_command("battery?", take_response=True)
                case _:
                    self.drone_communication.send_command("emergency")

        command = f"rc {for_backward:.2f} {left_right:.2f} {up_down} {yaw}"
        self.drone_communication.send_command(command, False)

    def get_ping(self):
        start_time = time.perf_counter_ns()
        self.drone_battery = self.drone_communication.send_command("battery?", take_response=True)
        end_time = time.perf_counter_ns()

        ping = (end_time - start_time) // 1000000
        
        print(f"Ping for communication: {ping} ms")
        
        self.drone_stats.delete("1.0", "end")
        self.drone_stats.insert("1.0", f"Battery: {self.drone_battery.strip()}% \nPing: {ping} ms")

    def main(self):
        while(self.running):
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
    TelloTkinterStream()
