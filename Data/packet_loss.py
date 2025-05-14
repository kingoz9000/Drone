import matplotlib.pyplot as plt

# Load cumulative loss data (%)
def load_loss_curve(filepath):
    with open(filepath, 'r') as f:
        return [float(x) for x in f.read().strip(", ").split(", ")]

# File paths for each test
files = {
    "1%": "Data/packet_loss_test/Data2025-05-09_11-18-14seq.txt",  # <-- the anomaly
    "5%": "Data/packet_loss_test/Data2025-05-09_11-21-54seq.txt",
    "10%": "Data/packet_loss_test/Data2025-05-09_11-23-51seq.txt",
    "20%": "Data/packet_loss_test/Data2025-05-09_11-26-55seq.txt",
    "50%": "Data/packet_loss_test/Data2025-05-09_11-28-47seq.txt",
}

# Plot
plt.figure(figsize=(10, 6))

for label, path in files.items():
    data = load_loss_curve(path)
    x = list(range(1, len(data) + 1))
    if label == "1%":
        plt.plot(x, data, label=label + " (anomaly)", color="red", linestyle="--", linewidth=2)
        # Optional annotation of the early spike
        early_max = max(data[:20])
        early_idx = data.index(early_max)
        plt.annotate(f"Early spike: {early_max:.1f}%",
                     xy=(early_idx, early_max),
                     xytext=(early_idx + 20, early_max + 5),
                     arrowprops=dict(arrowstyle="->", color="red"),
                     fontsize=9, color="red")
    else:
        plt.plot(x, data, label=label)

plt.xlabel("Packet Index")
plt.ylabel("Cumulative Packet Loss (%)")
plt.title("Cumulative Packet Loss Over Time")
plt.legend(title="Induced Loss")
plt.grid(True, linestyle="--", alpha=0.5)
plt.tight_layout()
plt.show()
