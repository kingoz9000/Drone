from collections import deque
import customtkinter as ctk

def init_ui_components(instance,plt,FigureCanvasTkAgg):
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