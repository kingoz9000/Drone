import matplotlib.pyplot as plt

# Data from your table
labels = [
    "Tello Mobile App",
    "Direct (WiFi)",
    "UDP Hole Punching",
    "Relayed (AAU VM)",
    "Relayed (Stockholm VM)"
]

# Use a small value for <1ms to allow bar plotting
rtt_values = [156, 201, 248, 259, 336]  # Replace "<1 ms" with a plausible 0.8 ms

# Bar colors (optional: more vibrant for readability)
colors = ['#5A5A5A', '#6C7EB2', '#8A9DC0', '#A8BCD0', '#C6DBE5']

# Create the plot
plt.figure(figsize=(9, 5))
bars = plt.bar(labels, rtt_values, color=colors)

# Annotate values on top of bars
for bar, rtt in zip(bars, rtt_values):
    plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2,
             f"{rtt} ms" if rtt > 1 else "<1 ms",
             ha='center', va='bottom', fontsize=10)

# Add the red line at y = 200
plt.axhline(y=200, color='red', linestyle='-', linewidth=2, label="Requirement: 200 ms")

# Titles and labels
plt.ylabel("Measured Video Latency (ms)")
plt.title("Average Video Latency by Data Path")
plt.ylim(0, 350)  # Provide room for text annotations

# Show gridlines
plt.grid(axis='y', linestyle='--', alpha=0.4)

# Add a legend
plt.legend()

plt.tight_layout()
plt.show()


def check_connection(self) -> None:
    """Check the connection status and trigger turn mode if necessary."""
    if (
        (self.avg_ping_ms > 200 or self.packet_loss > 4)
        and not self.stun_handler.turn_mode
        and self.ARGS.stun
    ):
        counter += 1
        if counter > 5: 
            print("Connection unstable, triggering turn mode")
            self.stun_handler.trigger_turn_mode()
            self.check_connection_thread.join(
    else:
        counter = 0

    time.sleep(1)


