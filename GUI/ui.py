from collections import deque
import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class UserInterface:
    def __init__(self, instance):
        self.instance = instance

    def init_ui_components(self, plt) -> None:

        self.instance.root.title("Tello Video Stream")
        self.instance.root.geometry(
            f"{int(1280*self.instance.scale)}x{int(1000*self.instance.scale)}"
        )
        self.instance.avg_ping_ms = 0
        self.instance.root.call("tk", "scaling", self.instance.scale)

        self.instance.root.protocol("WM_DELETE_WINDOW", self.instance.cleanup)
        self.instance.root.bind("<q>", lambda e: self.instance.cleanup())
        self.instance.root.bind("<t>", lambda e: self.instance.trigger_turnmode())

        self.instance.video_canvas = ctk.CTkCanvas(
            self.instance.root,
            width=int(960 * self.instance.scale),
            height=int(720 * self.instance.scale),
        )
        self.instance.video_canvas.pack(pady=20)
        self.instance.graph_frame = ctk.CTkFrame(
            self.instance.root,
            width=int(200 * self.instance.scale),
            height=int(500 * self.instance.scale),
        )
        self.instance.graph_frame.pack(side="left", padx=0, pady=0, anchor="s")

        background_color = "#242424"

        # --- Graph ---
        self.instance.fig, self.instance.ax = plt.subplots(figsize=(3, 2), dpi=100)
        self.instance.fig.patch.set_alpha(0)
        self.instance.ax.patch.set_alpha(0)
        self.instance.ax.tick_params(colors="white")
        self.instance.ax.set_title("Ping", color="white")
        self.instance.fig.patch.set_facecolor(background_color)
        self.instance.ax.set_facecolor(background_color)
        self.instance.ax.set_xlabel("Time (s)", color="white")
        self.instance.ax.set_ylabel("Ping (ms)", color="white")
        self.instance.ax.set_ylim(0, 150)
        self.instance.ping_data = deque([0] * 50, maxlen=50)
        (self.instance.line,) = self.instance.ax.plot(
            self.instance.ping_data, color="blue"
        )
        self.instance.canvas = FigureCanvasTkAgg(
            self.instance.fig, master=self.instance.graph_frame
        )
        canvas_widget = self.instance.canvas.get_tk_widget()
        canvas_widget.pack()
        canvas_widget.configure(bg=background_color, highlightthickness=0)

        # --- Battery Circle ---
        size = int(100 * self.instance.scale)
        self.instance.battery_canvas = ctk.CTkCanvas(
            self.instance.root,
            width=size,
            height=size,
            bg=background_color,
            highlightthickness=0,
        )
        self.instance.battery_canvas.place(
            relx=1.0, rely=1.0, anchor="se", x=-20, y=-20
        )
        self.instance.battery_canvas.create_oval(
            int(10 * self.instance.scale),
            int(10 * self.instance.scale),
            int(90 * self.instance.scale),
            int(90 * self.instance.scale),
            outline="white",
            width=2,
        )
        self.instance.battery_arc = self.instance.battery_canvas.create_arc(
            int(10 * self.instance.scale),
            int(10 * self.instance.scale),
            int(90 * self.instance.scale),
            int(90 * self.instance.scale),
            start=90,
            extent=0,
            fill="green",
            outline="",
        )
        self.instance.battery_canvas.create_text(
            int(50 * self.instance.scale),
            int(50 * self.instance.scale),
            text="Battery",
            fill="white",
            font=("Arial", int(8 * self.instance.scale)),
            tags="battery_text",
        )
        # --- Drone Stats Box ---
        self.instance.drone_stats_box = ctk.CTkTextbox(
            self.instance.root,
            height=int(150 * self.instance.scale),
            width=int(400 * self.instance.scale),
            bg_color=background_color,
        )
        self.instance.drone_stats_box.place(relx=0.5, rely=1.0, anchor="s", y=-10)
        self.instance.drone_stats_box.configure(
            state="disabled",
            font=("Arial", int(15 * self.instance.scale)),
            fg_color=background_color,
            text_color="white",
        )

        self.instance.drone_stats = ctk.CTkTextbox(
            self.instance.root,
            height=int(60 * self.instance.scale),
            width=int(340 * self.instance.scale),
        )
        self.instance.drone_stats.pack(pady=0)
        self.instance.drone_stats.insert("1.0", "Battery: xx% \nPing xx ms")
        self.instance.drone_stats.configure(state="disabled")

    def update_battery_circle(self) -> None:
        if self.instance.drone_battery and isinstance(self.instance.drone_battery, str):
            try:
                battery_level = int(self.instance.drone_battery.strip())

                text = f"{battery_level}%"
                self.instance.battery_canvas.itemconfig(
                    self.instance.battery_canvas.find_withtag("battery_text"), text=text
                )
                extent = (battery_level / 100) * 360
                self.instance.battery_canvas.itemconfig(
                    self.instance.battery_arc, extent=-extent
                )

                if battery_level > 50:
                    self.instance.battery_canvas.itemconfig(
                        self.instance.battery_arc, fill="green"
                    )
                elif battery_level > 20:
                    self.instance.battery_canvas.itemconfig(
                        self.instance.battery_arc, fill="orange"
                    )
                else:
                    self.instance.battery_canvas.itemconfig(
                        self.instance.battery_arc, fill="red"
                    )
            except ValueError:
                pass
