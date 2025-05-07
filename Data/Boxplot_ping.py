import matplotlib.pyplot as plt

# Load ping data from two files
def load_ping_data(filepath):
    with open(filepath, "r") as f:
        data = f.read().split(", ")
        return [int(num) for num in data]

data1 = load_ping_data("Data/2025-05-07_13-56-38ping.txt")
data2 = load_ping_data("Data/2025-05-07_14-03-08ping.txt")  # Replace with your second file

# Optional stats
print("File 1 - Min:", min(data1), "Max:", max(data1), "Mean:", sum(data1)/len(data1))
print("File 2 - Min:", min(data2), "Max:", max(data2), "Mean:", sum(data2)/len(data2))

# Plot two boxplots side by side
plt.figure(figsize=(8, 5))
plt.boxplot([data1, data2], vert=True, patch_artist=True,
            boxprops=dict(facecolor='skyblue', color='blue'),
            medianprops=dict(color='red'),
            whiskerprops=dict(color='gray'),
            capprops=dict(color='gray'),
            flierprops=dict(marker='o', markerfacecolor='orange', markersize=6, linestyle='none'))

plt.xticks([1, 2], ['Test 1', 'Test 2'])  # Custom labels
plt.ylabel("Ping (ms)")
plt.title("Ping Distribution Comparison")
plt.grid(True, linestyle='--', alpha=0.5)
plt.tight_layout()
plt.show()