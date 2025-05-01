import matplotlib.pyplot as plt
from collections import Counter

def analyze_file(filepath):
    with open(filepath, "r") as f:
        data = f.read()

    received_packets = [int(packet.strip()) for packet in data.split(",") if packet.strip().isdigit()]

    displacements = []
    reorder_count = 0

    for i in range(1, len(received_packets)):
        if received_packets[i] < received_packets[i - 1]:
            reorder_count += 1
            displacements.append(received_packets[i - 1] - received_packets[i])

    displacement_counter = Counter(displacements)
    total_packets = len(received_packets)

    return displacement_counter, reorder_count, total_packets

# File paths
file1 = "Data/Cellular_test_1/2025-04-24_12-22-52seq.txt"
file2 = "Data/Turn_test_1/2025-05-01_10-16-42seq.txt"  # Replace with your second file

# Analyze both files
disp1, reorder1, total1 = analyze_file(file1)
disp2, reorder2, total2 = analyze_file(file2)

# All unique displacements for consistent x-axis
all_displacements = sorted(set(disp1.keys()).union(disp2.keys()))

# Normalize to percentages
percentages1 = [100 * disp1.get(d, 0) / reorder1 if reorder1 else 0 for d in all_displacements]
percentages2 = [100 * disp2.get(d, 0) / reorder2 if reorder2 else 0 for d in all_displacements]

# Plot grouped bar chart
x = range(len(all_displacements))
width = 0.4

plt.figure(figsize=(10, 5))
plt.bar([i - width/2 for i in x], percentages1, width=width, label='Test 1', color='skyblue', edgecolor='black')
plt.bar([i + width/2 for i in x], percentages2, width=width, label='Test 2', color='lightgreen', edgecolor='black')

plt.xlabel('Displacement Amount')
plt.ylabel('Percentage of Reordered Packets (%)')
plt.title('Packet Reordering Displacement Comparison')
plt.xticks(x, all_displacements)
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.legend()
plt.tight_layout()
plt.show()