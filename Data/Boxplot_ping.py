import matplotlib.pyplot as plt

# Load ping data
with open("Data/Cellular_test_1/2025-04-24_12-23-01ping.txt", "r") as f:
    data = f.read()
    data = data.split(", ")
    data = [int(num) for num in data]

# Basic stats (optional, for reference)
print("Min:", min(data))
print("Max:", max(data))
print("Mean:", sum(data) / len(data))

# Plot boxplot
plt.figure(figsize=(6, 4))
plt.boxplot(data, vert=True, patch_artist=True,
            boxprops=dict(facecolor='skyblue', color='blue'),
            medianprops=dict(color='red'),
            whiskerprops=dict(color='gray'),
            capprops=dict(color='gray'),
            flierprops=dict(marker='o', markerfacecolor='orange', markersize=6, linestyle='none'))

plt.ylabel("Ping (ms)")
plt.title("Ping Distribution (Boxplot)")
plt.grid(True, linestyle='--', alpha=0.5)
plt.tight_layout()
plt.show()
