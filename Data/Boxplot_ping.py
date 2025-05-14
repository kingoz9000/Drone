import matplotlib.pyplot as plt

# Load ping data from files
def load_ping_data(filepath):
    with open(filepath, "r") as f:
        data = f.read().strip(", ").split(", ")
        return [int(num) for num in data]

# Load data
data1 = load_ping_data("Data/latency_test/2025-05-09_11-46-12ping.txt")
data2 = load_ping_data("Data/latency_test/2025-05-09_11-47-27ping.txt")
data3 = load_ping_data("Data/latency_test/2025-05-09_11-48-46ping.txt")
data4 = load_ping_data("Data/latency_test/2025-05-09_11-54-02ping.txt")

datasets = [data1, data2, data3, data4]
labels = ['+0ms', '+100ms', '+250ms', '+400ms']
induced_latencies = [0, 100, 250, 400]  # In ms

# Calculate average pings
averages = [sum(data) / len(data) for data in datasets]

# Calculate delta % from baseline (after subtracting induced latency)
baseline = averages[0]
deltas = []
for avg, induced in zip(averages, induced_latencies):
    adjusted = avg - induced
    try:
        delta = ((adjusted - baseline) / induced) * 100 if adjusted != 0 else 0
    except ZeroDivisionError:
        delta = 0
    deltas.append(round(delta))

# Print stats
for i, (avg, delta, induced) in enumerate(zip(averages, deltas, induced_latencies)):
    print(f"File {i+1} - Avg: {avg:.1f} ms, Induced: {induced} ms, Δ% from baseline: {delta}%")

# Plot
plt.figure(figsize=(9, 5))
plt.boxplot(datasets, vert=True, patch_artist=True,
            boxprops=dict(facecolor='skyblue', color='blue'),
            medianprops=dict(color='red'),
            whiskerprops=dict(color='gray'),
            capprops=dict(color='gray'),
            flierprops=dict(marker='o', markerfacecolor='orange', markersize=6, linestyle='none'))

plt.xticks([1, 2, 3, 4], labels)
plt.ylabel("Ping (ms)")
plt.title("Ping Distribution Comparison")
plt.grid(True, linestyle='--', alpha=0.5)

# Annotate averages and delta %
for i, (avg, delta) in enumerate(zip(averages, deltas)):
    if i == 3:
        # For data4 (index 3), place text below the box
        y_pos = min(datasets[i]) - 30
        va = 'top'
    else:
        y_pos = max(datasets[i]) + 10
        va = 'bottom'
    plt.text(i + 1, y_pos, f"{avg:.0f} ms\n({delta:+}%)",
             ha='center', va=va, fontsize=9, fontweight='bold')

plt.tight_layout()
plt.show()