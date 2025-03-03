from tkinter import Tk, Label


class TelloTkinterStream:
    def __init__(self):
        """Initialize Tkinter window and Tello video stream."""
        self.root = Tk()
        self.root.title("Tello Video Stream")
        self.root.geometry("1280x720")

        # Create a label to display the video
        self.video_label = Label(self.root)
        self.video_label.pack(fill="both", expand=True)


if __name__ == "__main__":
    TelloTkinterStream()
