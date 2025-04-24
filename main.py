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
        

        # Initialize the graph
        self.init_graph()
        
        # Create a frame for the stats
        self.stats_frame = ctk.CTkFrame(self.root, width=300, height=100)
        self.stats_frame.pack(side="right", fill="y", padx=20, pady=20)
        
        # Create a text box 
        self.stats_textbox = ctk.CTkTextbox(self.stats_frame, height=50, width=300)
        self.stats_textbox.pack(side="top", pady=10)

        # Bind cleanup to window close and q key
        self.root.protocol("WM_DELETE_WINDOW", self.cleanup)
        self.root.bind("<q>", lambda e: self.cleanup())

        self.stats_lock = threading.Lock() # thread safe UI updates
        self.connection_stats = {
            'battery': None, 
            'ping': None,
            'packet_loss': None,
            'packets': None
        }
        
        UI_stats = (
            f"Battery: {self.connection_stats['battery']}\n"
            f"Ping: {self.connection_stats['ping']}\n"
            f"Packet Loss: {self.connection_stats['packet_loss']}\n"
            f"Packets: {self.connection_stats['packets']}\n"            
        ) 
        
        # Show stats on UI
        self.print_to_image("1.0", UI_stats)
        
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

        # Start video stream and communication with the drone
        self.video_stream = DroneVideoFeed(drone_video_addr)

        self.connect_to_drone()
        self.drone_battery = None

        # Threads for joystick controls, pinging, and graph updates
        self.run_in_thread(self.control_drone)
        self.run_in_thread(self.get_ping)
        self.run_in_thread(self.update_graph)

        # Thread for packet loss measurement
        self.run_in_thread(self.get_packet_loss)

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
        self.ax.set_xlabel("Time (s)",color="white")
        self.ax.set_ylabel("Ping (ms)",color="white")
        self.ax.set_ylim(0, 150)
        #print(self.ax.get_facecolor())  
        
        
        self.ping_data = deque([0] * 50, maxlen=50)  # last 50 ping values
        self.line, = self.ax.plot(self.ping_data, color="blue")

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_frame)
        self.canvas.get_tk_widget().pack()
        self.canvas.get_tk_widget().configure(bg=background_color, highlightthickness=0)

    def update_graph(self):
        while True:
            self.ping_data.append(self.avg_ping_ms)
            self.line.set_ydata(self.ping_data)
            self.ax.set_xlim(0, len(self.ping_data))
            self.ax.set_ylim(0, max(max(self.ping_data), 150))
            #print(self.ax.get_facecolor())      
            self.canvas.draw()
            time.sleep(0.5)  

    def print_to_image(self, pos, text) -> None:
        self.drone_stats = ctk.CTkTextbox(self.root, height=50, width=300)
        self.drone_stats.pack(pady=10)
        self.drone_stats.insert(pos, text)
        self.drone_stats.configure(state="disabled")

    def update_stats(self) -> None:
        """Update the stats in the Tkinter window."""
        with self.stats_lock:
            self.drone_stats.delete("1.0", "end")
            self.drone_stats.insert(
                "1.0",
                f"Battery: {self.connection_stats['battery']}% \n"
                f"Ping: {self.connection_stats['ping']} ms \n"
                f"Packet loss: {self.connection_stats['packet loss']}% \n"
                f"Packets: {self.connection_stats['packets']}\n",
            )
        
    def get_peer_address(self) -> tuple:
        self.stun_handler = ControlStunClient()
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
            ping_ns = end_time - start_time
            ping_data.append(ping_ns)

            with open(file_name, "a") as file:
                file.write(f"{ping_ns}, ")

            self.avg_ping_ms = sum(ping_data) // len(ping_data) // 1_000_000

            self.drone_stats.configure(state="normal")
            self.drone_stats.delete("1.0", "end")
            if type(self.drone_battery) is str:
                with self.stats_lock:
                    self.connection_stats['ping'] = f"{self.avg_ping_ms:03d} ms"
                    self.connection_stats['battery'] = f"{self.drone_battery.strip()}%"
                    self.update_stats()
                time.sleep(0.2)
            else:
                self.drone_stats.insert(
                    "1.0", f"Bad connection! Lost packages\nPing: {self.avg_ping_ms:03d}+ ms"
                )
            self.drone_stats.configure(state="disabled")

    def get_packet_loss(self) -> None:
        """Check for packet loss and update the UI accordingly."""
        if self.ARGS.noloss:
            return

        packets_sent = []
        packets_received = []
        total_packets_sent = 0
        total_packets_received = 0
        SAMPLE_SIZE = 100  # Number of packets per test

        while True:
            if self.ARGS.stun:
                for _ in range(SAMPLE_SIZE):
                    try:
                        # send test packet
                        test_packet_response = self.stun_handler.send_command(
                            "command", False, True
                        )
                        packets_sent.append(1)
                        total_packets_sent += 1
                        if test_packet_response is not None:  # track pakckets
                            packets_received.append(1)  # success
                            total_packets_received += 1
                        else:
                            packets_received.append(0)  # failure

                        # continually update the packet loss
                        if len(packets_sent) > SAMPLE_SIZE:
                            packets_sent.pop(0)
                            packets_received.pop(0)
                        time.sleep(0.01)
                    
                    except Exception as e:
                        print(f"Error in packet loss measurment: {e}")
                        break

                packets_received_sum = sum(packets_received)
                packets_sent_count = len(packets_sent)
                if packets_sent_count > 0:
                    # Calculate packet loss percentage
                    packet_loss = (
                        (packets_sent_count - packets_received_sum)
                        / packets_sent_count
                        * 100
                    )
                else:
                    packet_loss = 0.00

                # update UI
                with self.stats_lock:
                    self.connection_stats['packet loss'] = f"{packet_loss:.2f}%"
                    self.connection_stats['packets'] = f"{total_packets_received} / {total_packets_sent}"
                    self.update_stats()
                time.sleep(0.1)  # delay to avoid overwhelming the UI

    def cleanup(self) -> None:
        """Safely clean up resources and close the customTkinter window."""
        print("Shutting down...")

        self.send_command("streamoff")

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
    parser.add_argument(
        "-nl", "--noloss", help="Disable packet loss", action="store_true"
    )
    args = parser.parse_args()

    TelloCustomTkinterStream(args)
