import matplotlib.pyplot as plt

# Load and clean data from file
def load_delays(filename):
    with open(filename, 'r') as file:
        lines = file.read().split(', ')
    # Remove whitespace and convert to float, skip invalid lines
    delays = []
    for line in lines:
        try:
            delay = float(line.strip())
            delays.append(delay)
        except ValueError:
            continue
    return delays

# Plot histogram
def plot_histogram(delays):
    plt.figure(figsize=(10, 6))
    plt.hist(delays, bins=200, color='skyblue', edgecolor='black')
    plt.title("Histogram of Packet Delays (ms)")
    plt.xlabel("Delay (ms)")
    plt.ylabel("Frequency")
    plt.yscale('log')  # Log scale helps to see small clusters and large outliers
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    delays = load_delays("size.txt")
    print(delays.count(1460) / len(delays))
    plot_histogram(delays)

