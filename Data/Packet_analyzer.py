import matplotlib.pyplot as plt
# Convert to list of integers
datafile = "Data/Ethernet_test_1/2025-04-29_17-48-15seq.txt"  # Replace with your data file path

#recieved packets are in datafile seperated by comma
with open(datafile, "r") as f:
    data = f.read()
# to int

received_packets = data.split(",")

# convert to int
received_packets = [int(packet.strip()) for packet in received_packets if packet.strip().isdigit()]

# Analyze reordering
displacements = []
reorder_count = 0
expected_packet = received_packets[0]

for i, packet in enumerate(received_packets):
    if i == 0:
        continue
    if packet < received_packets[i - 1]:
        reorder_count += 1
        displacement = received_packets[i - 1] - packet
        displacements.append(displacement)

# Count the most common displacement
from collections import Counter
displacement_counter = Counter(displacements)
most_common_displacement = displacement_counter.most_common(1)[0] if displacement_counter else None

# Total packets
total_packets = len(received_packets)

print(f"Total packets: {total_packets}, max_number: {max(received_packets)}")

reorder_frequency = reorder_count / total_packets

reorder_count, reorder_frequency, most_common_displacement


displacement_percentages = {
    displacement: (count, (count / reorder_count) * 100)
    for displacement, count in displacement_counter.items()
}

# Sort by most common
sorted_displacement_percentages = dict(sorted(displacement_percentages.items(), key=lambda x: x[1][0], reverse=True))

# Print results
print("Displacement percentages:")
for displacement, (count, percentage) in sorted_displacement_percentages.items():
    print(f"Displacement {displacement}: {count} packets ({percentage:.2f}%)")

# generate histogram

# Output
print(f"Total packets: {total_packets}")
print(f"Reordered packets: {reorder_count}")
print(f"Reorder frequency: {reorder_frequency:.2%}")
if most_common_displacement:
    print(f"Most common displacement: {most_common_displacement[0]} with count {most_common_displacement[1]}")


counts = [sorted_displacement_percentages[d][0] for d in displacements]

plt.figure(figsize=(10, 5))
plt.bar(displacements, counts, color='skyblue', edgecolor='black')
plt.xlabel('Displacement Amount')
plt.ylabel('Number of Packets')
plt.title('Histogram of Packet Displacements')
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.xticks(displacements)
plt.tight_layout()
plt.show()

# 16 ms per package

