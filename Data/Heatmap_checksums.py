import matplotlib.pyplot as plt
import numpy as np

def load_checksum_data(path):
    checksums = []
    with open(path, 'r') as f:
        for line in f:
            if 'checksum:' in line:
                # Extract checksum value between 'checksum:' and ','
                checksum_hex = line.split('checksum:')[1].split(',')[0].strip()
                # Convert hex string to bytes and then to list of integers
                checksum_bytes = bytes.fromhex(checksum_hex)
                checksums.append(list(checksum_bytes))
    return checksums

def create_checksum_heatmap(relay_path, controller_path):
    relay_checksums = load_checksum_data(relay_path)
    controller_checksums = load_checksum_data(controller_path)
    
    # Convert to numpy arrays for easier manipulation
    relay_array = np.array(relay_checksums)
    controller_array = np.array(controller_checksums)
    
    # Calculate differences
    min_len = min(len(relay_array), len(controller_array)) 
    differences = np.abs(relay_array[:min_len] - controller_array[:min_len]) 
    
    # Create heatmap
    plt.figure(figsize=(12, 6))
    plt.imshow(differences.T, aspect='auto', cmap='YlOrRd')
    plt.colorbar(label='Byte Difference')
    plt.xlabel('Sequence Number')
    plt.ylabel('Byte Position')
    plt.title('Checksum Differences Between Relay and Controller')
    plt.tight_layout()
    plt.show()


relay_file = "Data/relay_checksums.txt"
controller_file = "Data/controller_checksums.txt"
create_checksum_heatmap(relay_file, controller_file)

