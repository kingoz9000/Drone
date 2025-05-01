import heapq
import threading
import time
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
        encoded = command.encode()
        if self.turn_mode:
            encoded = bytearray([8]) + encoded

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

    def disconnect_from_stunserver(self):
        self.stun_socket.sendto(b"DISCONNECT", self.STUN_SERVER_ADDR)
        self.stun_socket.close()
        self.running = False

    def handle_flags(self, data):
        file_name = f"{time.strftime('%Y-%m-%d_%H-%M-%S', time.localtime())}seq.txt"

        reorder_buffer: list[tuple] = []
        self.min_buffer_size = 6
        last_seq_num = 0

        if not self.relay and self.hole_punched:
            # Loopback for the operator
            flag = data[0]

            # If 0 send to loopback (videofeed)
            if flag == 0:
                seq_num = int.from_bytes(data[1:4], "big")
                payload = data[4:]

                # print(f"From client: {seq_num}")
                if self.log:
                    with open("Data/" + file_name, "a") as writer:
                        writer.write(f"{seq_num}, ")

                heapq.heappush(reorder_buffer, (seq_num, payload))

                if len(reorder_buffer) >= self.min_buffer_size:
                    ordered_seq, ordered_data = heapq.heappop(reorder_buffer)

                    if ordered_seq != last_seq_num + 1:
                        print(f"Expected: {last_seq_num + 1}, Got: {ordered_seq}")

                    self.stun_socket.sendto(ordered_data, ("127.0.0.1", 27463))
                    # video_file.write(ordered_data)
                    last_seq_num = ordered_seq

                    # Measure packet loss
                    self.seq_numbers[last_seq_num % 1000] = last_seq_num
                    self.packet_loss = (
                        (max(self.seq_numbers) - min(self.seq_numbers) - 999) / 1000
                    ) * 100
                    self.packet_loss = self.packet_loss if self.packet_loss >= 0 else 0
                return True

            # Response
            elif flag == 1:
                # Skal sendes til TKinter
                self.response.put(data[1:])
                return True

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
                return True
