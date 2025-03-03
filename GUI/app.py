from tkinter import Tk, Label
from PIL import Image, ImageTk
from drone_communication import DroneCommunication
from joystick import JoystickHandler
import threading


class TelloTkinterStream:
    def __init__(self):
        """Initialize Tkinter window and Tello video stream."""
        self.root: Tk = Tk()
        self.root.title("Tello Video Stream")
        self.root.geometry("1280x720")

        # Create a label to display the video
        self.video_label: Label = Label(self.root)
        self.video_label.pack(fill="both", expand=True)

        # Start video stream
        self.video_stream: DroneCommunication = DroneCommunication()
        self.video_stream.main()

        # Initialize joystick
        self.joystick = JoystickHandler()
        self.run_in_thread(self.joystick.start_reading)

        self.control_drone()

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
        x, y, z, buttons = self.joystick.get_values()
        up_down = 0
        yaw = 0
        weight = 0.5

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
                case 8:
                    self.video_stream.send_command("takeoff")
                case 9:
                    self.video_stream.send_command("land")
                case _:
                    self.video_stream.send_command("emergency")
                    

        command = f"rc {x*100*weight:.2f} {-(y*100*weight):.2f} {up_down} {yaw}"
        print(command)
        self.video_stream.send_command(command)

        self.root.after(10, self.control_drone)


if __name__ == "__main__":
    TelloTkinterStream()
