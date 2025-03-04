from tkinter import Tk, Label, Entry
from PIL import Image, ImageTk
from drone_communication import DroneCommunication
from joystick import JoystickHandler
import threading
import time


class TelloTkinterStream:
    def __init__(self):
        """Initialize Tkinter window and Tello video stream."""
        self.root: Tk = Tk()
        self.root.title("Tello Video Stream")
        self.root.geometry("1280x720")

        # Create a label to display the video
        self.video_label: Label = Label(self.root)
        self.video_label.pack(fill="both", expand=True)

        self.drone_stats = Entry(self.root)
        self.drone_stats.pack()

        # Start video stream
        self.video_stream: DroneCommunication = DroneCommunication()
        self.video_stream.main()

        # Initialize joystick
        self.joystick = JoystickHandler()
        self.run_in_thread(self.joystick.start_reading)

        # Initialize drone class
        self.drone = Drone()

        # Start joystick control and ping loops
        self.control_drone()
        self.get_ping()

        # Start video update loop
        self.update_video_frame()

        # Bind cleanup to window close
        self.root.protocol("WM_DELETE_WINDOW", self.cleanup)

        # Bind keys
        self.root.bind("q", lambda e: self.cleanup())

        # Start Tkinter event loop
        self.root.mainloop()

    def update_video_frame(self) -> None:
        """Update the video frame at 100 FPS (every 10ms)."""
        # Get the latest frame from the queue
        frame = self.video_stream.get_frame()

        if frame is not None:
            try:
                # Convert the frame to an ImageTk object
                img = Image.fromarray(frame)
                imgtk = ImageTk.PhotoImage(image=img)
                self.video_label.imgtk = imgtk
                self.video_label.config(image=imgtk)
            except Exception as e:
                print(f"Error updating video frame: {e}")

        # Call this function again in 10ms *Can be adjusted*
        self.root.after(10, self.update_video_frame)

    def cleanup(self) -> None:
        """Safely clean up resources and close the Tkinter window."""
        print("Shutting down...")

        self.video_stream.stop()
        self.root.quit()
        self.root.destroy()

    @staticmethod
    def run_in_thread(func, *args) -> threading.Thread:
        """General worker function to run a function in a thread"""
        thread = threading.Thread(target=func, args=args, daemon=True)
        thread.start()
        return thread

    def control_drone(self):
        # Weights and other values
        deadzone = 3

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
                    up_down -= 100 * weight
                case 3:
                    up_down += 100 * weight
                case 4:
                    yaw -= 100 * weight
                case 5:
                    yaw += 100 * weight
                case 6:
                    self.video_stream.send_command("reboot")
                case 8:
                    self.video_stream.send_command("takeoff")
                case 9:
                    self.video_stream.send_command("land")
                case 10:
                    self.video_stream.send_command("battery?", take_response=True)
                case _:
                    self.video_stream.send_command("emergency")

        command = f"rc {for_backward:.2f} {left_right:.2f} {up_down} {yaw}"
        self.video_stream.send_command(command, False)

        self.root.after(10, self.control_drone)

    def get_ping(self):
        start_time = time.perf_counter_ns()
        self.drone.battery = self.video_stream.send_command("battery?", take_response=True)
        end_time = time.perf_counter_ns()
        
        print(f"Ping for communication: {(end_time - start_time) // 1000} ms")

        self.drone_stats.insert(0, self.drone.battery)

        self.root.after(1000, self.get_ping)


class Drone():
    def __init__(self):
        self.battery = None


if __name__ == "__main__":
    TelloTkinterStream()
