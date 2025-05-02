import argparse
import math
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
from webserver.webserver_sender import WebserverSender


class TelloCustomTkinterStream:
    def __init__(self, args) -> None:
        """Starts GUI, drone communication, video stream & threads needed for stats and control."""
        self.ARGS = args

        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")
        self.scale = self.ARGS.rasmus if self.ARGS.rasmus else 1.0
        self.root = ctk.CTk()

        init_ui_components(self, plt, FigureCanvasTkAgg)

        self.init_drone_com()

        if self.ARGS.webstream:
            self.webserver_sender = WebserverSender()
            self.run_in_thread(self.webserver_sender.ffmpeg_writer)

        self.run_in_thread(self.control_drone)
        self.run_in_thread(self.get_ping)
        self.run_in_thread(self.fetch_and_update_drone_stats)
        self.run_in_thread(self.check_connection)

        self.update_video_frame()

        self.root.mainloop()

    def init_drone_com(self) -> None:
        """Initialize drone communication and video stream."""
        if self.ARGS.stun:
            self.stun_handler = ControlStunClient(self.ARGS.log)
            self.peer_addr = self.get_peer_address()
            time.sleep(5)
            self.drone_video_addr = ("0.0.0.0", 27463)
            self.send_command = self.stun_handler.send_command_to_relay
        else:
            self.drone_video_addr = ("0.0.0.0", 11111)
            self.drone_comm_addr = ("192.168.10.1", 8889)
            self.drone_communication = DroneCommunication(self.drone_comm_addr, 9000)
            self.send_command = self.drone_communication.send_command
            self.run_in_thread(self.drone_communication.wifi_state_socket_handler)

        self.video_stream = DroneVideoFeed(self.drone_video_addr)
        self.startup_drone()
        self.drone_battery = None

    def fetch_and_update_drone_stats(self) -> None:
        """Fetch and update drone stats in a loop."""
        while True:
            try:
                if self.ARGS.stun:
                    stats = self.stun_handler.get_drone_stats()
                else:
                    stats = self.drone_communication.get_direct_drone_stats()

            except Exception as e:
                print(f"Error fetching stats: {e}")
            self.update_drone_stats(stats)
            time.sleep(1)

    def update_graph(self) -> None:
        """Update the graph with the latest ping data."""
        self.ping_data.append(self.avg_ping_ms)
        self.line.set_ydata(self.ping_data)
        self.ax.set_xlim(0, len(self.ping_data))
        self.ax.set_ylim(0, max(max(self.ping_data), 150))

        # print(self.ax.get_facecolor())
        self.canvas.draw()

    def update_drone_stats(self, stats) -> None:
        """Update the drone stats in the GUI."""
        if not isinstance(stats, dict):
            print("Error: stats is not a dictionary")
            return

        self.packet_loss = self.stun_handler.packet_loss if self.ARGS.stun else 0

        stats_text = (
            f"Pitch: {stats.get('pitch', 0)}°\n"
            f"Roll: {stats.get('roll', 0)}°\n"
            f"Yaw: {stats.get('yaw', 0)}°\n"
            f"Altitude: {stats.get('baro', 0)} m\n"
            f"Speed: {math.sqrt((stats.get('vgx', 0))**2 + (stats.get('vgy', 0))**2 + (stats.get('vgz', 0))**2)} m/s\n"
            f"Board temperature: {stats.get('temph', 0)} °C\n"
            f"Packet loss: {round(self.packet_loss,2)} %\n"
        )

        self.drone_stats_box.configure(state="normal")
        self.drone_stats_box.delete("1.0", "end")
        self.drone_stats_box.insert("1.0", stats_text)
        self.drone_stats_box.configure(state="disabled")

        update_battery_circle(self)
        self.update_graph()

    def get_peer_address(self) -> tuple:
        """Get the peer address when using stun argument."""
        self.stun_handler.main()
        for _ in range(10):
            if self.stun_handler.hole_punched:
                print("Peer to Peer connection established")
                return self.stun_handler.get_peer_addr()
            time.sleep(1)

        raise Exception("Failed to establish peer-to-peer connection")

    def startup_drone(self) -> None:
        """Sends startup commands to the drone."""
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
                if self.ARGS.webstream and self.webserver_sender.ffmpeg_process:
                    resized = cv2.resize(frame, (640, 480))
                    if not self.webserver_sender.frame_queue.full():
                        self.webserver_sender.frame_queue.put_nowait(resized)

                self.root.after(0, self.update_canvas, imgtk)

            except Exception as e:
                print(f"Error updating video frame: {e}")

        self.root.after(10, self.update_video_frame)

    def update_canvas(self, imgtk) -> None:
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
            if not self.drone_battery == "ERROR":
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

    def trigger_turnmode(self) -> None:
        print("Triggering turn mode...")
        if self.ARGS.stun:
            self.stun_handler.trigger_turn_mode()
            # change plot color to orange
            self.line.set_color("orange")

    def check_connection(self) -> None:
        """Check the connection status and trigger turn mode if necessary."""
        if (
            self.avg_ping_ms > 300
            and self.packet_loss > 5
            and not self.stun_handler.turn_mode
            and self.ARGS.stun
        ):
            print("Connection unstable, triggering turn mode")
            self.stun_handler.trigger_turn_mode()
            time.sleep(1)

    def cleanup(self) -> None:
        """Safely clean up resources and close the customTkinter window."""
        print("Shutting down...")

        self.send_command("streamoff")
        self.send_command("motoroff")

        if self.ARGS.stun:
            self.stun_handler.disconnect_from_stun_server()

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
