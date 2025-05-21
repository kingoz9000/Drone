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
    
    print(f"{filepath} - Packet reordering: {reorder_count/total_packets:.2%}")

    return displacement_counter, reorder_count, total_packets

# File paths
file1 = "Data/Holep.txt"
file2 = "Data/Turn.txt"  # Change this to your second file path

# Analyze both files
disp1, reorder1, total1 = analyze_file(file1)
disp2, reorder2, total2 = analyze_file(file2)

# Union of all displacement values for a consistent x-axis
all_displacements = sorted(set(disp1.keys()) | set(disp2.keys()))

# Normalize to percentages
percentages1 = [100 * disp1.get(d, 0) / reorder1 if reorder1 else 0 for d in all_displacements]
percentages2 = [100 * disp2.get(d, 0) / reorder2 if reorder2 else 0 for d in all_displacements]

# Plotting side-by-side
x = range(len(all_displacements))
width = 0.35

plt.figure(figsize=(12, 6))
plt.bar([i - width/2 for i in x], percentages1, width=width, color='#6C7EB2', label='Hole punch', edgecolor='black', zorder=3)
plt.bar([i + width/2 for i in x], percentages2, width=width, color='#B26C6C', label='Turn', edgecolor='black', zorder=3)

plt.xlabel('Displacement Amount')
plt.ylabel('Percentage of Reordered Packets (%)')
plt.title('Packet Reordering Displacement Comparison')
plt.xticks(x, all_displacements)
plt.ylim(0, max(percentages1 + percentages2) + 5)
plt.legend()
plt.grid(axis='y', linestyle='--', alpha=0.7, zorder=0)

plt.tight_layout()
plt.show()