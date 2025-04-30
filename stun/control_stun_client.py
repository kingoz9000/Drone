import heapq
import threading
import time
import socket
from queue import Queue

from .stun_client import StunClient


class ControlStunClient(StunClient):
    def __init__(self, log):
        super().__init__()
        self.response = Queue()
        self.log = log
        self.drone_stats = {}
        self.stats_lock = threading.Lock()
        self.packet_loss = 0
        self.seq_numbers = [0 for _ in range(1000)]

    def send_command_to_relay(self, command, print_command=False, take_response=False):
        if self.turn_mode:
            command = f"RELAY {command}"

        self.stun_socket.sendto(command.encode(), self.sending_addr)
        self.uplink_data_size += len(command.encode()) # track uplink data size

    def get_peer_addr(self):
        if self.peer_addr:
            return self.peer_addr

    def get_drone_stats(self):
        with self.stats_lock:
            stats = self.drone_stats.copy()
        return stats

    def trigger_turn_mode(self):
        self.stun_socket.sendto(b"REQUEST_TURN_MODE", self.STUN_SERVER_ADDR)

    def disconnect_from_stunserver(self):
        self.stun_socket.sendto(b"DISCONNECT", self.STUN_SERVER_ADDR)
        self.stun_socket.close()
        self.running = False
        
    def calculate_bandwidth(self):
        elapsed_time = time.time() - self.bandwidth_start_time
        if elapsed_time > 0:  
            # Calculate uplink and downlink bandwidth in bits per second
            uplink_bps = (self.uplink_data_size * 8) / elapsed_time # bytes are converted to bits
            downlink_bps = (self.downlink_data_size * 8) / elapsed_time
            self.uplink_mbps = uplink_bps / 1_000_000 # bits are converted to megabits
            self.downlink_mbps = downlink_bps / 1_000_000
            
            # reset the counters
            self.uplink_data_size = 0
            self.downlink_data_size = 0
            self.bandwidth_start_time = time.time()  # reset the start time
            
    def listen(self):
        file_name = f"{time.strftime('%Y-%m-%d_%H-%M-%S', time.localtime())}seq.txt"

        reorder_buffer: list[tuple] = []
        MIN_BUFFER_SIZE = 6
        last_seq_num = 0
        # Open this once before your loop starts

        # video_file = open("output_stream.h264", "ab")  # append in binary mode

        while self.running:
            data = self.stun_socket.recv(4096)
            self.downlink_data_size += len(data) # track downlink data size

            if not self.relay and self.hole_punched:
                # Loopback for the operator
                flag = data[0]

                # If 0 send to loopback (videofeed)
                if flag == 0:
                    seq_num = int.from_bytes(data[1:3], "big")
                    payload = data[3:]

                    # print(f"From client: {seq_num}")
                    if self.log:
                        with open("Data/" + file_name, "a") as writer:
                            writer.write(f"{seq_num}, ")

                    heapq.heappush(reorder_buffer, (seq_num, payload))

                    if len(reorder_buffer) >= MIN_BUFFER_SIZE:
                        ordered_seq, ordered_data = heapq.heappop(reorder_buffer)

                        if ordered_seq != last_seq_num + 1:
                            print(f"Expected: {last_seq_num + 1}, Got: {ordered_seq}")

                        self.stun_socket.sendto(ordered_data, ("127.0.0.1", 27463))
                        # video_file.write(ordered_data)
                        last_seq_num = ordered_seq

                        # Measure packet loss
                        self.seq_numbers[last_seq_num % 1000] = last_seq_num
                        self.packet_loss = ((max(self.seq_numbers) - min(self.seq_numbers) - 999) / 1000) * 100 
                        self.packet_loss = self.packet_loss if self.packet_loss >= 0 else 0
                    continue

                # Response
                elif flag == 1:
                    # Skal sendes til TKinter
                    self.response.put(data[1:])
                    continue

                # State
                elif flag == 2:
                    drone_data = data[1:]
                    try:
                        drone_data = drone_data.decode().strip().strip(";").split(";")
                        for part in drone_data:
                            key, value = part.split(":")
                            if "," in value:
                                with self.stats_lock:
                                    self.drone_stats[key] = tuple(
                                        map(float, value.split(","))
                                    )
                            else:
                                try:
                                    with self.stats_lock:
                                        self.drone_stats[key] = (
                                            float(value) if "." in value else int(value)
                                        )
                                except ValueError:
                                    with self.stats_lock:
                                        self.drone_stats[key] = value
                    except Exception as e:
                        print(f"Error in decoding: {e}")

                    continue

            message = data.decode()

            if message.startswith("SERVER"):
                if message.split()[1] == "CONNECT":
                    _, _, peer_ip, peer_port = message.split()
                    print(f"Received peer details: {peer_ip}:{peer_port}")
                    self.peer_addr = (peer_ip, int(peer_port))
                    self.sending_addr = self.peer_addr
                    self.hole_punch()
                    self.is_connected = True

                if message.split()[1] == "INVALID_ID":
                    print("Invalid target ID.")

                if message.split()[1] == "HEARTBEAT":
                    self.stun_socket.sendto(b"ALIVE", self.STUN_SERVER_ADDR)

                if message.split()[1] == "DISCONNECT":
                    print("Server disconnected due to other client disconnection")
                    self.stun_socket.close()
                    self.running = False

                if message.split()[1] == "CLIENTS":
                    print(f"Clients connected: {message}")
                    self.request_peer()
                if message.split()[1] == "TURN_MODE":
                    print("Turn mode activated.")
                    self.sending_addr = self.STUN_SERVER_ADDR
                    self.turn_mode = True
                    continue

            if message.startswith("HOLE") and not self.hole_punched:
                self.hole_punched = True
                print("Hole punched!")
                self.stun_socket.sendto(b"HOLE PUNCHED", self.STUN_SERVER_ADDR)

            if message.startswith("PEER"):
                # intended for the relay
                continue
            print(f"Received message: {message}")
