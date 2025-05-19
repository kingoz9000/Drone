import matplotlib.pyplot as plt
import numpy as np

# Labels for each test path
labels = [
    "Tello Mobile App",
    "Direct (WiFi)",
    "UDP Hole Punching",
    "Relayed (AAU VM)",
    "Relayed (Stockholm VM)"
]

# Data for each test
rtt_values_picture_test = [156, 201, 248, 259, 336]
sd_values_picture_test = [28, 26, 35, 15, 27]

rtt_values_blinker_test = [226, 204, 286, 283, 334]
sd_values_blinker_test = [101, 52, 49, 44, 53]

# Bar settings
x = np.arange(len(labels))  # Label locations
width = 0.35  # Width of the bars

# Create the plot
fig, ax = plt.subplots(figsize=(10, 6))

# Plot both sets of bars
bars1 = ax.bar(x - width/2, rtt_values_picture_test, width, yerr=sd_values_picture_test,
               label='Picture Test', capsize=5, color='#6C7EB2', zorder=2)
bars2 = ax.bar(x + width/2, rtt_values_blinker_test, width, yerr=sd_values_blinker_test,
               label='Blinker Test', capsize=5, color='#A8BCD0', zorder=2)

# Add annotation labels
def annotate_bars(bars):
    for bar in bars:
        height = bar.get_height()
        ax.annotate(f'{int(height)} ms',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=9)

annotate_bars(bars1)
annotate_bars(bars2)

# Reference line
ax.axhline(y=200, color='red', linestyle='-', linewidth=1.5, label="Requirement: 200 ms", zorder=3)

# Formatting
ax.set_ylabel('Video Latency (ms)')
ax.set_title('Average Video Latency by Data Path')
ax.set_xticks(x)
ax.set_xticklabels(labels, rotation=15)
ax.set_ylim(0, 400)
ax.legend()
ax.grid(axis='y', linestyle='--', alpha=0.5, zorder=0)

plt.tight_layout()
plt.show()