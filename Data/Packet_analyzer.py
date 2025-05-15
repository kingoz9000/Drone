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
    
    print(f"packet reordering: {reorder_count/total_packets:.2%}")

    return displacement_counter, reorder_count, total_packets

# File path for the first file only
file1 = "Data/Celleular_packet_reordering"

# Analyze the first file
disp1, reorder1, total1 = analyze_file(file1)

# All unique displacements for consistent x-axis
all_displacements = sorted(disp1.keys())

# Normalize to percentages
percentages1 = [100 * disp1.get(d, 0) / reorder1 if reorder1 else 0 for d in all_displacements]

# Plot the bar chart
x = range(len(all_displacements))
width = 0.5

plt.figure(figsize=(10, 5))
plt.bar(x, percentages1, width=width, color='#6C7EB2', edgecolor='black', zorder=3)  # Use a more scientific color

# Titles and labels
plt.xlabel('Displacement Amount')
plt.ylabel('Percentage of Reordered Packets (%)')
plt.title('Packet Reordering Displacement Test for Cellular Connection')
plt.xticks(x, all_displacements)
plt.ylim(0, max(percentages1) + 5)  # Give some space at the top for better visibility
plt.grid(axis='y', linestyle='--', alpha=0.7, zorder=0)

plt.tight_layout()
plt.show()
