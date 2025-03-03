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

        #thread = threading.Thread(target=self.joystick, args=args, daemon=True)
        #thread.start()

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

    def read_joystick(self):
        x, y, z, buttons = self.joystick.get_values()

        self.video_stream.send_command

if __name__ == "__main__":
    TelloTkinterStream()
