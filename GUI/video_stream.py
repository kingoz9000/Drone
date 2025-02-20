import cv2
import threading
from tkinter import Tk, Label
from PIL import Image, ImageTk
from djitellopy import Tello
import time

class TelloTkinterStream:
    def __init__(self):
        """Initialize Tkinter window and Tello video stream."""
        self.root = Tk()
        self.root.title("Tello Video Stream")
        self.root.geometry("1280x720")  # Start with a larger size
        self.root.resizable(True, True)  # Allow resizing

        # Create a label to display the video
        self.video_label = Label(self.root)
        self.video_label.pack(fill="both", expand=True)  # Expand with window resize

        # Initialize Tello drone
        self.drone = Tello()
        self.drone.connect()
        print(f"Battery: {self.drone.get_battery()}%")
        
        # Start video stream
        self.drone.streamon()
        self.frame_reader = self.drone.get_frame_read()
        self.running = True

        # Start video update loop in a separate thread
        self.video_thread = threading.Thread(target=self.video_loop, daemon=True)
        self.video_thread.start()

        # Handle window resizing
        self.root.bind("<Configure>", self.on_resize)

        # Handle window close event
        self.root.protocol("WM_DELETE_WINDOW", self.cleanup)

        # Run Tkinter event loop
        self.root.mainloop()

    def on_resize(self, event):
        """Handles window resizing and adjusts the frame size dynamically."""
        self.window_width = event.width
        self.window_height = event.height

    def video_loop(self):
        """Runs the video stream in a separate thread while updating Tkinter UI correctly."""
        while self.running:
            frame = self.frame_reader.frame  # Get the latest frame
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2BGRA)  # Convert to RGB
            
            # Resize frame to match window size
            frame = cv2.resize(frame, (self.root.winfo_width(), self.root.winfo_height()))

            # Convert frame to a Tkinter-compatible format
            img = Image.fromarray(frame)
            imgtk = ImageTk.PhotoImage(image=img)

            # Update the label in the main thread using `after`
            self.root.after(1, self.update_label, imgtk)

    def update_label(self, imgtk):
        """Updates the Tkinter Label in the main thread to prevent flickering."""
        self.video_label.imgtk = imgtk
        self.video_label.configure(image=imgtk)

    def cleanup(self):
        """Cleanup resources when closing the window."""
        print("Stopping video stream...")
        self.running = False
        self.drone.streamoff()
        self.drone.end()
        self.root.destroy()

if __name__ == "__main__":
    TelloTkinterStream()

