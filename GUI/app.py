import threading
from tkinter import Tk, Label
from PIL import Image, ImageTk
import time
from video_stream_reciever import DroneCommunication

class TelloTkinterStream:
    def __init__(self):
        """Initialize Tkinter window and Tello video stream."""
        self.root = Tk()
        self.root.title("Tello Video Stream")
        self.root.geometry("1280x720")

        # Create a label to display the video
        self.video_label = Label(self.root)
        self.video_label.pack(fill="both", expand=True)

        # Start video stream
        self.video_stream = DroneCommunication()
        self.video_stream.main()

        # Start video update loop
        self.update_video_frame()

        self.root.protocol("WM_DELETE_WINDOW", self.cleanup)
        self.root.mainloop()  # Start the Tkinter event loop

    def update_video_frame(self):
        """Efficiently update the video frame at 100 FPS (every 10ms)."""
        frame = self.video_stream.get_frame()

        if frame is not None:
            try:
                img = Image.fromarray(frame)
                imgtk = ImageTk.PhotoImage(image=img)
                self.video_label.imgtk = imgtk
                self.video_label.config(image=imgtk)
            except Exception as e:
                print(f"Error updating video frame: {e}")

        self.root.after(10, self.update_video_frame)  # Faster updates (10ms instead of 30ms)

    def cleanup(self):
        """Safely clean up resources and close the Tkinter window."""
        print("Shutting down...")

        self.video_stream.stop()  # Stop video stream
        self.root.quit()  # Quit Tkinter event loop
        self.root.destroy()  # Destroy the window

if __name__ == "__main__":
    TelloTkinterStream()

