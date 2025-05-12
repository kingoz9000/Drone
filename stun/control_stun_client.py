import heapq
import threading
import time
from queue import Queue

from .stun_client import StunClient


class ControlStunClient(StunClient):
    def __init__(self, log):
        super().__init__()
        self.response: list[str] = Queue()
        self.log: list[str] = log
        self.drone_stats: dict[str] = {}
        self.stats_lock = threading.Lock()
        self.packet_loss: int = 0
        self.received_seq_set = set()

        self.file_name = (
            f"{time.strftime('%Y-%m-%d_%H-%M-%S', time.localtime())}seq.txt"
        )
        self.reorder_buffer: list[tuple] = []
        self.min_buffer_size = 6
        self.last_seq_num = -1

    def send_command_to_relay(self, command, print_command=False, take_response=False):
        encoded = command.encode()
        if self.turn_mode:
            encoded = bytearray([16]) + encoded

        self.stun_socket.sendto(encoded, self.sending_addr)

    def get_peer_addr(self):
        if self.peer_addr:
            return self.peer_addr

    def get_drone_stats(self):
        with self.stats_lock:
            stats = self.drone_stats.copy()
        return stats

    def trigger_turn_mode(self):
        self.stun_socket.sendto(b"REQUEST_TURN_MODE", self.STUN_SERVER_ADDR)

    def disconnect_from_stun_server(self):
        self.stun_socket.sendto(b"DISCONNECT", self.STUN_SERVER_ADDR)
        self.stun_socket.close()
        self.running = False

    def handle_flags(self, data):
        if not self.relay and self.hole_punched:
            # Loopback for the operator
            flag = data[0]

            # If 0 send to loopback (videofeed)
            if flag == 1:
                seq_num = int.from_bytes(data[1:4], "big")
                payload = data[4:]

                # print(f"From client: {seq_num}")
                if self.log:
                    with open("Data/" + self.file_name, "a") as writer:
                        writer.write(f"{seq_num}, ")

                heapq.heappush(self.reorder_buffer, (seq_num, payload))

                if len(self.reorder_buffer) >= self.min_buffer_size:
                    ordered_seq, ordered_data = heapq.heappop(self.reorder_buffer)

                    if ordered_seq != self.last_seq_num + 1:
                        print(f"Expected: {self.last_seq_num + 1}, Got: {ordered_seq}")

                    self.stun_socket.sendto(ordered_data, ("127.0.0.1", 27463))
                    # video_file.write(ordered_data)
                    self.last_seq_num = ordered_seq

                    self.received_seq_set.add(ordered_seq)

                    # Limit size to last 250 entries (close to 4 seconds according to requrements)
                    if len(self.received_seq_set) > 250:
                        self.received_seq_set.remove(min(self.received_seq_set))

                    # Calculate packet loss
                    if len(self.received_seq_set) >= 2:
                        expected_range = (
                            max(self.received_seq_set) - min(self.received_seq_set) + 1
                        )
                        received_count = len(self.received_seq_set)
                        lost_count = expected_range - received_count
                        self.packet_loss = (lost_count / expected_range) * 100
                    else:
                        self.packet_loss = 0.0

                return True

            # Response
            elif flag == 2:
                # Skal sendes til TKinter
                data = data[1:].decode()
                if data:
                    self.response.put(data)
                return True

            # State
            elif flag == 3:
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
                return True

            # Bandwidth test
            elif flag == 4:
                payload = data[1:]
                if not hasattr(self, "bandwidth_start_time"):
                    self.bandwidth_start_time = time.time()
                    self.received_bandwidth_data = 0

                self.received_bandwidth_data += len(payload)

                elapsed_time = time.time() - self.bandwidth_start_time
                if elapsed_time >= 1.0:  # every second
                    bandwidth = (
                        self.received_bandwidth_data / elapsed_time
                    )  # Bytes per second
                    bandwidth_kb = bandwidth / 1024  # Convert to KB/s
                    print(f"Bandwidth: {bandwidth_kb:.2f} KB/sec")
                    self.bandwidth_start_time = time.time()
                    self.received_bandwidth_data = 0
                return True

    def listen(self):
        while self.running:
            data = self.stun_socket.recv(4096)
            self.handle_flags(data):
            message = data.decode()

            if message.startswith("SERVER"):
                self.handle_server_messages(message)
                continue
            if message.startswith("HOLE") and not self.hole_punched:
                self.handle_hole_punch_message()
                continue

            print("Unhanled command/message:", message)


    def main(self):
        self.register()
        self._run_in_thread(self.listen)
