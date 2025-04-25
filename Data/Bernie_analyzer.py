import matplotlib.pyplot as plt

def load_seq_data(path):
    with open(path, "r") as f:
        data = f.read()
    return [int(x.strip()) for x in data.strip().split(",")]

def load_ping_data(path):
    with open(path, "r") as f:
        data = f.read()
    return [float(x.strip()) for x in data.strip().split(",")]

def detect_out_of_order(seq_list):
    out_of_order = []
    max_seen = -1
    for s in seq_list:
        if s < max_seen:
            out_of_order.append(True)
        else:
            out_of_order.append(False)
            max_seen = s
    return out_of_order

def bin_out_of_order(flags, bin_size):
    binned = []
    for i in range(0, len(flags), bin_size):
        chunk = flags[i:i + bin_size]
        binned.append(sum(chunk))
    return binned

def moving_average(data, window):
    if window < 1:
        return data
    return [sum(data[max(0, i - window + 1):i + 1]) / min(i + 1, window) for i in range(len(data))]

def compute_ping_deltas(ping_values):
    return [ping_values[i] - ping_values[i - 1] for i in range(1, len(ping_values))]

def plot_combined(out_of_order_counts, ping_deltas, bin_size, ma_window=5):
    # Smooth both datasets
    smoothed_oop = moving_average(out_of_order_counts, ma_window)
    smoothed_ping_deltas = moving_average(ping_deltas, ma_window)

    # Time axes
    time_bins = [i * bin_size for i in range(len(out_of_order_counts))]
    ping_time = [i * (len(time_bins) / len(ping_deltas)) * bin_size for i in range(len(ping_deltas))]

    fig, ax1 = plt.subplots(figsize=(12, 5))

    ax1.set_xlabel("Time (approx. by bins)")
    ax1.set_ylabel("Out-of-Order Packets", color="tab:red")
    ax1.plot(time_bins, out_of_order_counts, label="Raw OOP", color="lightcoral", linestyle="--", alpha=0.5)
    ax1.plot(time_bins, smoothed_oop, label=f"Smoothed OOP (win={ma_window})", color="tab:red", linewidth=2)
    ax1.tick_params(axis='y', labelcolor="tab:red")

    ax2 = ax1.twinx()
    ax2.set_ylabel("Δ Ping (ms)", color="tab:blue")
    ax2.plot(ping_time, ping_deltas, label="Raw ΔPing", color="skyblue", linestyle=":", marker="x", alpha=0.5)
    ax2.plot(ping_time, smoothed_ping_deltas, label=f"Smoothed ΔPing (win={ma_window})", color="tab:blue", linewidth=2)
    ax2.tick_params(axis='y', labelcolor="tab:blue")

    fig.tight_layout()
    ax1.legend(loc="upper left")
    ax2.legend(loc="upper right")
    plt.title("Out-of-Order Packets vs Δ Ping (with Moving Averages)")
    plt.grid(True)
    plt.show()

# --- Run it ---
seq_path = "Cellular_test_1/2025-04-24_12-22-52seq.txt"
ping_path = "Cellular_test_1/2025-04-24_12-23-01ping.txt"

seq_data = load_seq_data(seq_path)
ping_data = load_ping_data(ping_path)

out_of_order_flags = detect_out_of_order(seq_data)
bin_size = 20  # packets per time interval

binned_out_of_order = bin_out_of_order(out_of_order_flags, bin_size)
ping_deltas = compute_ping_deltas(ping_data)

plot_combined(binned_out_of_order, ping_deltas, bin_size, ma_window=5)
