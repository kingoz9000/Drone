import matplotlib.pyplot as plt

# Data
labels = ["0%", "1%", "5%", "10%", "20%", "50%"]
induced = [0, 1, 5, 10, 20, 50]
measured = [0.09, 1.05, 4.76, 10.37, 19.85, 50.03]
delta = [4, 7, 3, 1, 0]

x = range(len(labels))
width = 0.35

fig, ax1 = plt.subplots(figsize=(10, 5))

# Bar plot for induced and measured
bars1 = ax1.bar([i - width/2 for i in x], induced, width=width, label="Induced", color="#A0C4FF", edgecolor='black', zorder=3)
bars2 = ax1.bar([i + width/2 for i in x], measured, width=width, label="Measured", color="#BDB2FF", edgecolor='black', zorder=3)

# Annotate measured values above bars
for i, val in enumerate(measured):
    ax1.text(i + width/2, val + 0.6, f"{val:.2f}%", ha='center', va='bottom', fontsize=9)

# Labels and grid for left axis
ax1.set_ylabel("Packet Loss (%)")
ax1.set_xticks(x)
ax1.set_xticklabels(labels)
ax1.grid(axis='y', linestyle='--', alpha=0.3, zorder=0)

# Twin axis for delta %
ax2 = ax1.twinx()
ax2.plot([1,2,3,4,5], delta, color="#FF595E", marker='o', linewidth=2, label="Δ% from baseline", zorder=4)
ax2.set_ylabel("Δ% from Baseline")

# Titles and legend
fig.suptitle("Induced vs Measured Packet Loss and Δ% from Baseline", fontsize=14)
fig.legend(loc="upper left", bbox_to_anchor=(0.07, 0.9))

plt.tight_layout()
plt.show()
