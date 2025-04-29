import argparse, threading, time
from collections import deque

import customtkinter as ctk
from joystick.button_mapping import ButtonMap
from GUI.drone_communication import DroneCommunication
from GUI.drone_video_feed import DroneVideoFeed
from PIL import Image, ImageTk
from stun import ControlStunClient
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class TelloCustomTkinterStream:
    def __init__(self, args):
        self.ARGS = args

        # Initialize customTkinter window and Tello video stream.
        ctk.set_appearance_mode("Dark")  # Options: "System", "Dark", "Light"
        ctk.set_default_color_theme("blue")  # Options: "blue", "green", "dark-blue"

        self.root = ctk.CTk()
        self.root.title("Tello Video Stream")
        self.root.geometry("1280x1000")
        self.avg_ping_ms = 0

        # Create a canvas to display the video
        self.video_canvas = ctk.CTkCanvas(self.root, width=960, height=720)
        self.video_canvas.pack(pady=20)

        # Create a frame for the graph
        self.graph_frame = ctk.CTkFrame(self.root, width=200, height=500)
        self.graph_frame.pack(side="left", padx=0, pady=0, anchor="s")

        self.init_graph()
        self.init_battery_circle()
        self.init_drone_stats()

        # Bind cleanup to window close and q key
        self.root.protocol("WM_DELETE_WINDOW", self.cleanup)
        self.root.bind("<q>", lambda e: self.cleanup())

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
            self.run_in_thread(
                self.drone_communication.wifi_state_socket_handler
            )  # Grab stats directly from drone

        # Start video stream and communication with the drone
        self.video_stream = DroneVideoFeed(drone_video_addr)

        self.connect_to_drone()
        self.drone_battery = None

        # Threads for joystick controls, pinging, and graph updates
        self.run_in_thread(self.control_drone)
        self.run_in_thread(self.get_ping)
        self.run_in_thread(self.update_graph)
        self.run_in_thread(self.update_battery_circle)
        self.run_in_thread(self.fetch_and_update_drone_stats)

        # Start video update loop
        self.update_video_frame()

        # Start customTkinter event loop
        self.root.mainloop()

    def init_graph(self):
        self.fig, self.ax = plt.subplots(figsize=(3, 2), dpi=100)
        self.fig.patch.set_alpha(0)
        self.ax.patch.set_alpha(0)
        background_color = "#242424"
        self.ax.tick_params(colors="white")
        self.ax.set_title("Ping", color="white")
        self.fig.patch.set_facecolor(background_color)
        self.ax.set_facecolor(background_color)
        self.ax.set_xlabel("Time (s)", color="white")
        self.ax.set_ylabel("Ping (ms)", color="white")
        self.ax.set_ylim(0, 150)
        # print(self.ax.get_facecolor())

        self.ping_data = deque([0] * 50, maxlen=50)  # last 50 ping values
        (self.line,) = self.ax.plot(self.ping_data, color="blue")

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_frame)
        self.canvas.get_tk_widget().pack()
        self.canvas.get_tk_widget().configure(bg=background_color, highlightthickness=0)

    def init_battery_circle(self):
        self.battery_canvas = ctk.CTkCanvas(
            self.root, width=100, height=100, bg="#242424", highlightthickness=0
        )
        self.battery_canvas.place(
            relx=1.0, rely=1.0, anchor="se", x=-20, y=-20
        )  # Lower-right corner with padding

        self.battery_canvas.create_oval(10, 10, 90, 90, outline="white", width=2)

        self.battery_arc = self.battery_canvas.create_arc(
            10, 10, 90, 90, start=90, extent=0, fill="green", outline=""
        )
        self.battery_canvas.create_text(
            50, 50, text="Battery", fill="white", font=("Arial", 8), tags="battery_text"
        )

    def init_drone_stats(self):
        self.drone_stats_box = ctk.CTkTextbox(
            self.root, height=150, width=400, bg_color="#242424"
        )
        self.drone_stats_box.place(
            relx=0.5, rely=1.0, anchor="s", y=-10
        )  # Bottom center
        self.drone_stats_box.configure(
            state="disabled", font=("Arial", 15), fg_color="#242424", text_color="white"
        )

    def update_drone_stats(self, pitch, roll, yaw, altitude, speed, battery):
        stats_text = (
            f"Pitch: {pitch}°\n"
            f"Roll: {roll}°\n"
            f"Yaw: {yaw}°\n"
            f"Altitude: {altitude} m\n"
            f"Speed: {speed} m/s\n"
            f"Battery: {battery}%"
        )
        self.drone_stats_box.configure(state="normal")
        self.drone_stats_box.delete("1.0", "end")
        self.drone_stats_box.insert("1.0", stats_text)
        self.drone_stats_box.configure(state="disabled")

    def get_drone_stats(self):
        try:
            if self.ARGS.stun:
                stats = self.stun_handler.get_drone_stats()
            else:
                # get stats directly from drone
                stats = self.drone_communication.stats 

            pitch = stats.get("pitch", 0)
            roll = stats.get("roll", 0)
            yaw = stats.get("yaw", 0)
            altitude = 0
            speed = stats.get("vgx", 0)
            board_temp = stats.get("temph", 0)

            return pitch, roll, yaw, altitude, speed, board_temp
        except Exception as e:
            print(f"Error fetching stats: {e}")
            return 0, 0, 0, 0, 0, 0


    def fetch_and_update_drone_stats(self):
        while True:
            pitch, roll, yaw, altitude, speed, board_temp = self.get_drone_stats()
            self.update_drone_stats(pitch, roll, yaw, altitude, speed, board_temp)
            time.sleep(1)

    def update_battery_circle(self):
        while True:
            if self.drone_battery and isinstance(self.drone_battery, str):
                try:
                    battery_level = int(self.drone_battery.strip())

                    text = f"{battery_level}%"
                    self.battery_canvas.itemconfig(
                        self.battery_canvas.find_withtag("battery_text"), text=text
                    )
                    extent = (battery_level / 100) * 360
                    self.battery_canvas.itemconfig(self.battery_arc, extent=-extent)

                    if battery_level > 50:
                        self.battery_canvas.itemconfig(self.battery_arc, fill="green")
                    elif battery_level > 20:
                        self.battery_canvas.itemconfig(self.battery_arc, fill="orange")
                    else:
                        self.battery_canvas.itemconfig(self.battery_arc, fill="red")
                except ValueError:
                    pass

            time.sleep(5)

    def update_graph(self):
        while True:
            self.ping_data.append(self.avg_ping_ms)
            self.line.set_ydata(self.ping_data)
            self.ax.set_xlim(0, len(self.ping_data))
            self.ax.set_ylim(0, max(max(self.ping_data), 150))
            # print(self.ax.get_facecolor())
            self.canvas.draw()
            time.sleep(0.5)

    def update_drone_stats(self, pitch, roll, yaw, altitude, speed, board_temp):
        stats_text = (
            f"Pitch: {pitch}°\n"
            f"Roll: {roll}°\n"
            f"Yaw: {yaw}°\n"
            f"Altitude: {altitude} m\n"
            f"Speed: {speed} m/s\n"
            f"Board temperature: {board_temp}%"
        )
        self.drone_stats_box.configure(state="normal")
        self.drone_stats_box.delete("1.0", "end")
        self.drone_stats_box.insert("1.0", stats_text)
        self.drone_stats_box.configure(state="disabled")

    def print_to_image(self, pos, text) -> None:
        self.drone_stats = ctk.CTkTextbox(self.root, height=50, width=300)
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

    def update_video_frame(self) -> None:
        """Update the video frame in the customTkinter window."""
        frame = self.video_stream.get_frame()
        if frame is not None:
            try:
                img = Image.fromarray(frame)

                # Resize the image
                img = img.resize((960, 720), Image.Resampling.LANCZOS)

                imgtk = ImageTk.PhotoImage(image=img)

                # Update the canvas using the main thread
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
    args = parser.parse_args()

    TelloCustomTkinterStream(args)
