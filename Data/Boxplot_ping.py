import matplotlib.pyplot as plt
import statistics

# Load ping data from files
def load_ping_data(filepath):
    with open(filepath, "r") as f:
        data = f.read().strip(", ").split(", ")
        return [int(num) for num in data]

# Load data
data1 = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
data2 = load_ping_data("Data/Testing_sec/Stun/2025-05-07_13-56-38ping.txt")
data3 = load_ping_data("Data/Testing_sec/Strato/2025-05-07_14-03-08ping.txt")
data4 = load_ping_data("Data/Testing_sec/Stockholm/2025-05-07_14-00-02ping.txt")

data1 = sorted(data1)
#print(statistics.stdev())

data2 = sorted(data2)
#print(statistics.stdev(sorted(data2)[:-3]))

data3 = sorted(data3)[:-3]
#print(statistics.stdev(sorted(data3)[:-3]))

data4 = sorted(data4)[:-5]
#print(statistics.stdev(sorted(data4)[:-3]))


datasets = [data1, data2, data3, data4]
labels = ['Direct (Wifi)', 'Peer-To-Peer', 'Relayed (AAU VM)', 'Relayed (Stockholm VM)']
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

plt.ylim(-10, 200)
plt.xticks([1, 2, 3, 4], labels)
plt.ylabel("Ping (ms)")
plt.title("Ping Distribution Comparison")
plt.grid(True, linestyle='--', alpha=0.5)

# Annotate averages and delta %
for i, (avg, delta) in enumerate(zip(averages, deltas)):
    # For data4 (index 3), place text below the box
    y_pos = min(datasets[i]) - 3
    va = 'top'
    plt.text(i + 1, y_pos, f"{avg:.0f} ms",
             ha='center', va=va, fontsize=9, fontweight='bold')

plt.tight_layout()
plt.show()