from collections import deque
import customtkinter as ctk

def init_ui_components(instance,plt,FigureCanvasTkAgg):


    instance.root.title("Tello Video Stream")
    instance.root.geometry(f"{int(1280*instance.scale)}x{int(1000*instance.scale)}")
    instance.avg_ping_ms = 0
    instance.root.call("tk", "scaling", instance.scale)

    instance.root.protocol("WM_DELETE_WINDOW", instance.cleanup)
    instance.root.bind("<q>", lambda e: instance.cleanup())
    instance.root.bind("<t>", lambda e: instance.trigger_turnmode())

    
    instance.video_canvas = ctk.CTkCanvas(
        instance.root, width=int(960 * instance.scale), height=int(720 * instance.scale)
    )
    instance.video_canvas.pack(pady=20)
    instance.graph_frame = ctk.CTkFrame(
        instance.root, width=int(200 * instance.scale), height=int(500 * instance.scale)
    )
    instance.graph_frame.pack(side="left", padx=0, pady=0, anchor="s")    
    
    
    
    background_color = "#242424"
    
    # --- Graph ---
    instance.fig, instance.ax = plt.subplots(figsize=(3, 2), dpi=100)
    instance.fig.patch.set_alpha(0)
    instance.ax.patch.set_alpha(0)
    instance.ax.tick_params(colors="white")
    instance.ax.set_title("Ping", color="white")
    instance.fig.patch.set_facecolor(background_color)
    instance.ax.set_facecolor(background_color)
    instance.ax.set_xlabel("Time (s)", color="white")
    instance.ax.set_ylabel("Ping (ms)", color="white")
    instance.ax.set_ylim(0, 150)
    instance.ping_data = deque([0] * 50, maxlen=50)
    (instance.line,) = instance.ax.plot(instance.ping_data, color="blue")
    instance.canvas = FigureCanvasTkAgg(instance.fig, master=instance.graph_frame)
    canvas_widget = instance.canvas.get_tk_widget()
    canvas_widget.pack()
    canvas_widget.configure(bg=background_color, highlightthickness=0)

    # --- Battery Circle ---
    size = int(100 * instance.scale)
    instance.battery_canvas = ctk.CTkCanvas(
        instance.root, width=size, height=size, bg=background_color, highlightthickness=0
    )
    instance.battery_canvas.place(relx=1.0, rely=1.0, anchor="se", x=-20, y=-20)
    instance.battery_canvas.create_oval(
        int(10 * instance.scale), int(10 * instance.scale), int(90 * instance.scale), int(90 * instance.scale),
        outline="white", width=2
    )
    instance.battery_arc = instance.battery_canvas.create_arc(
        int(10 * instance.scale), int(10 * instance.scale), int(90 * instance.scale), int(90 * instance.scale),
        start=90, extent=0, fill="green", outline=""
    )
    instance.battery_canvas.create_text(
        int(50 * instance.scale), int(50 * instance.scale),
        text="Battery", fill="white", font=("Arial", int(8 * instance.scale)),
        tags="battery_text"
    )
    # --- Drone Stats Box ---
    instance.drone_stats_box = ctk.CTkTextbox(
        instance.root,
        height=int(150 * instance.scale),
        width=int(400 * instance.scale),
        bg_color=background_color
    )
    instance.drone_stats_box.place(relx=0.5, rely=1.0, anchor="s", y=-10)
    instance.drone_stats_box.configure(
        state="disabled",
        font=("Arial", int(15 * instance.scale)),
        fg_color=background_color,
        text_color="white"
    )

    instance.drone_stats = ctk.CTkTextbox(
        instance.root, height=int(60 * instance.scale), width=int(340 * instance.scale)
    )
    instance.drone_stats.pack(pady=0)
    instance.drone_stats.insert("1.0", "Battery: xx% \nPing xx ms")
    instance.drone_stats.configure(state="disabled")

def update_battery_circle(instance):
    if instance.drone_battery and isinstance(instance.drone_battery, str):
        try:
            battery_level = int(instance.drone_battery.strip())

            text = f"{battery_level}%"
            instance.battery_canvas.itemconfig(
                instance.battery_canvas.find_withtag("battery_text"), text=text
            )
            extent = (battery_level / 100) * 360
            instance.battery_canvas.itemconfig(instance.battery_arc, extent=-extent)

            if battery_level > 50:
                instance.battery_canvas.itemconfig(instance.battery_arc, fill="green")
            elif battery_level > 20:
                instance.battery_canvas.itemconfig(instance.battery_arc, fill="orange")
            else:
                instance.battery_canvas.itemconfig(instance.battery_arc, fill="red")
        except ValueError:
            pass