import argparse
import math
import queue
import socket
import subprocess
import threading
import time
from collections import deque

import customtkinter as ctk
import cv2
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from PIL import Image, ImageTk

from GUI.drone_communication import DroneCommunication
from GUI.drone_video_feed import DroneVideoFeed
from GUI.ui import init_ui_components, update_battery_circle
from joystick.button_mapping import ButtonMap
from stun import ControlStunClient

FFMPEG_COMMAND = [
    "ffmpeg",
    "-y",
    "-f",
    "rawvideo",
    "-vcodec",
    "rawvideo",
    "-pix_fmt",
    "bgr24",
    "-s",
    "640x480",  # width x height of frames
    "-r",
    "30",
    "-i",
    "-",  # input from stdin
    "-c:v",
    "libx264",
    "-x264-params",
    "keyint=30:min-keyint=30:scenecut=0",
    "libx264",
    "-preset",
    "veryfast",
    "-tune",
    "zerolatency",
    "-f",
    "mpegts",
    "udp://130.225.37.157:27463",
]


class TelloCustomTkinterStream:
    def __init__(self, args):
        self.ARGS = args

        # Initialize customTkinter window and Tello video stream.
        ctk.set_appearance_mode("Dark")  # Options: "System", "Dark", "Light"
        ctk.set_default_color_theme("blue")  # Options: "blue", "green", "dark-blue"
        self.scale = self.ARGS.rasmus if self.ARGS.rasmus else 1.0
        self.root = ctk.CTk()
        self.root.title("Tello Video Stream")
        self.root.geometry(f"{int(1280*self.scale)}x{int(1000*self.scale)}")
        self.avg_ping_ms = 0

        self.root.call("tk", "scaling", self.scale)

        # Create a canvas to display the video
        self.video_canvas = ctk.CTkCanvas(
            self.root, width=int(960 * self.scale), height=int(720 * self.scale)
        )
        self.video_canvas.pack(pady=20)

        # Create a frame for the graph
        self.graph_frame = ctk.CTkFrame(
            self.root, width=int(200 * self.scale), height=int(500 * self.scale)
        )
        self.graph_frame.pack(side="left", padx=0, pady=0, anchor="s")

        init_ui_components(self, plt, FigureCanvasTkAgg)

        # Bind cleanup to window close and q key
        self.root.protocol("WM_DELETE_WINDOW", self.cleanup)
        self.root.bind("<q>", lambda e: self.cleanup())

        self.print_to_image("1.0", "Battery: xx% \nPing xx ms")

        if args.stun:
            self.peer_addr = self.get_peer_address()
            time.sleep(5)
            drone_video_addr = ("0.0.0.0", 27463)
            self.send_command = self.stun_handler.send_command_to_relay
            self.WEBSERVER_IP = "130.225.37.157"
            self.WEBSERVER_PORT = 27463
            self.webserver_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            if self.ARGS.stun and self.ARGS.webstream:
                self.ffmpeg_process = subprocess.Popen(
                    FFMPEG_COMMAND, stdin=subprocess.PIPE
                )
                self.frame_queue = queue.Queue(maxsize=10)
                self.run_in_thread(self.ffmpeg_writer)
            else:
                self.ffmpeg_process = None
        else:
            drone_video_addr = ("0.0.0.0", 11111)
            drone_comm_addr = ("192.168.10.1", 8889)
            self.drone_communication = DroneCommunication(drone_comm_addr, 9000)
            self.send_command = self.drone_communication.send_command
            self.run_in_thread(self.drone_communication.wifi_state_socket_handler)

        # Start video stream and communication with the drone
        self.video_stream = DroneVideoFeed(drone_video_addr)

        self.connect_to_drone()
        self.drone_battery = None

        # Threads for joystick controls, pinging, and graph updates
        self.run_in_thread(self.control_drone)
        self.run_in_thread(self.get_ping)
        self.run_in_thread(self.fetch_and_update_drone_stats)

        # Start video update loop
        self.update_video_frame()

        # Start customTkinter event loop
        self.root.mainloop()

    def ffmpeg_writer(self):
        while True:
            frame = self.frame_queue.get()
            try:
                self.ffmpeg_process.stdin.write(frame.tobytes())
            except Exception as e:
                print(f"FFmpeg write error: {e}")

    def fetch_and_update_drone_stats(self):
        while True:
            try:
                if self.ARGS.stun:
                    stats = self.stun_handler.get_drone_stats()
                else:
                    # get stats directly from drone
                    stats = self.drone_communication.get_direct_drone_stats()

            except Exception as e:
                print(f"Error fetching stats: {e}")
            self.update_drone_stats(stats)
            time.sleep(1)

    def update_graph(self):
        self.ping_data.append(self.avg_ping_ms)
        self.line.set_ydata(self.ping_data)
        self.ax.set_xlim(0, len(self.ping_data))
        self.ax.set_ylim(0, max(max(self.ping_data), 150))
        # print(self.ax.get_facecolor())
        self.canvas.draw()

    def update_drone_stats(self, stats):
        if not isinstance(stats, dict):
            print("Error: stats is not a dictionary")
            return

        stats_text = (
            f"Pitch: {stats.get('pitch', 0)}°\n"
            f"Roll: {stats.get('roll', 0)}°\n"
            f"Yaw: {stats.get('yaw', 0)}°\n"
            f"Altitude: {stats.get('baro', 0)} m\n"
            f"Speed: {math.sqrt((stats.get('vgx', 0))**2 + (stats.get('vgy', 0))**2 + (stats.get('vgz', 0))**2)} m/s\n"
            f"Board temperature: {stats.get('temph', 0)} °C"
        )

        self.drone_stats_box.configure(state="normal")
        self.drone_stats_box.delete("1.0", "end")
        self.drone_stats_box.insert("1.0", stats_text)
        self.drone_stats_box.configure(state="disabled")

        update_battery_circle(self)
        self.update_graph()

    def print_to_image(self, pos, text) -> None:
        self.drone_stats = ctk.CTkTextbox(
            self.root, height=int(50 * self.scale), width=int(300 * self.scale)
        )
        self.drone_stats.pack(pady=10)
        self.drone_stats.insert(pos, text)
        self.drone_stats.configure(state="disabled")

    def get_peer_address(self) -> tuple:
        self.stun_handler = ControlStunClient(self.ARGS.log)
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
        self.send_command("motoron")

    def update_video_frame(self) -> None:
        """Update the video frame in the customTkinter window."""
        frame = self.video_stream.get_frame()
        if frame is not None:
            try:
                img = Image.fromarray(frame)

                # Resize the image
                img = img.resize(
                    (int(960 * self.scale), int(720 * self.scale)),
                    Image.Resampling.LANCZOS,
                )

                imgtk = ImageTk.PhotoImage(image=img)
                # Update the canvas using the main thread
                self.root.after(0, self.update_canvas, imgtk)

                if self.ARGS.stun and self.ARGS.webstream and self.webserver_socket:
                    # Compress frame as JPEG
                    resized = cv2.resize(frame, (640, 480))
                    if self.ffmpeg_process:
                        if hasattr(self, "frame_queue") and not self.frame_queue.full():
                            self.frame_queue.put_nowait(resized)

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

        file_name = (
            f"Data/{time.strftime('%Y-%m-%d_%H-%M-%S', time.localtime())}ping.txt"
        )

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
            ping_ms = (end_time - start_time) // 1_000_000
            ping_data.append(ping_ms)

            if self.ARGS.log:
                with open(file_name, "a") as file:
                    file.write(f"{ping_ms}, ")

            self.avg_ping_ms = sum(ping_data) // len(ping_data)

            self.drone_stats.configure(state="normal")
            self.drone_stats.configure(font=("Arial", int(15 * self.scale)))
            self.drone_stats.configure()
            self.drone_stats.delete("1.0", "end")

            if type(self.drone_battery) is str:
                self.drone_stats.insert(
                    "1.0",
                    f"Battery: {self.drone_battery.strip()}% \nPing: {self.avg_ping_ms:03d} ms",
                )
                time.sleep(0.2)
            else:
                self.drone_stats.insert(
                    "1.0",
                    f"Bad connection! Lost packages\nPing: {self.avg_ping_ms:03d}+ ms",
                )
            self.drone_stats.configure(state="disabled")

    def cleanup(self) -> None:
        """Safely clean up resources and close the customTkinter window."""
        print("Shutting down...")

        self.send_command("streamoff")

        if self.ARGS.stun:
            self.stun_handler.disconnect_from_stunserver()

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
    parser.add_argument("-l", "--log", help="Log data", action="store_true")
    parser.add_argument(
        "-r", "--rasmus", help="Rasmus scaling", type=float, default=1.0
    )
    parser.add_argument("-w", "--webstream", help="Use webstream", action="store_true")
    args = parser.parse_args()

    TelloCustomTkinterStream(args)
