import heapq
import threading
import time
from queue import Queue

from .stun_client import StunClient


class ControlStunClient(StunClient):
    def __init__(self, log):
        super().__init__()
        self.response: Queue = Queue()
        self.log: list[str] = log
        self.drone_stats: dict = {}
        self.stats_lock = threading.Lock()
        self.packet_loss: float = 0
        self.received_seq_set: set = set()

        self.file_name: str = (
            f"{time.strftime('%Y-%m-%d_%H-%M-%S', time.localtime())}seq.txt"
        )
        self.reorder_buffer: list[tuple] = []
        self.min_buffer_size: int = 8
        self.last_seq_num: int = -1

    def send_command_to_relay(
        self, command, print_command=False, take_response=False
    ) -> None:
        encoded = command.encode()
        if self.turn_mode:
            encoded = bytearray([16]) + encoded

        if self.sending_addr:
            self.stun_socket.sendto(encoded, self.sending_addr)

    def get_peer_addr(self) -> tuple[str, int] | None:
        if self.peer_addr:
            return self.peer_addr

    def get_drone_stats(self) -> dict:
        with self.stats_lock:
            return self.drone_stats.copy()

    def trigger_turn_mode(self) -> None:
        self.stun_socket.sendto(b"SWITCH TURN MODE", self.STUN_SERVER_ADDR)

    def disconnect_from_stun_server(self) -> None:
        self.stun_socket.sendto(b"DISCONNECT", self.STUN_SERVER_ADDR)
        self.stun_socket.close()
        self.running = False

    def send_videofeed(self, data) -> None:
        seq_num = int.from_bytes(data[1:4], "big")
        payload = data[4:]

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

    def respond(self, data) -> None:
        data = data[1:].decode()
        if data:
            self.response.put(data)

    def state(self, data) -> None:
        drone_data = data[1:]
        try:
            drone_data = drone_data.decode().strip().strip(";").split(";")
            for part in drone_data:
                key, value = part.split(":")
                if "," in value:
                    with self.stats_lock:
                        self.drone_stats[key] = tuple(map(float, value.split(",")))
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

    def bandwidth_test(self, data) -> None:
        payload = data[1:]
        if not hasattr(self, "bandwidth_start_time"):
            self.bandwidth_start_time = time.time()
            self.received_bandwidth_data = 0

        self.received_bandwidth_data += len(payload)

        elapsed_time = time.time() - self.bandwidth_start_time
        if elapsed_time >= 1.0:  # every second
            bandwidth = self.received_bandwidth_data / elapsed_time  # Bytes per second
            bandwidth_kb = bandwidth / 1024  # Convert to KB/s
            print(f"Bandwidth: {bandwidth_kb:.2f} KB/sec")
            self.bandwidth_start_time = time.time()
            self.received_bandwidth_data = 0

    def listen(self) -> None:
        while self.running:
            data = self.stun_socket.recv(4096)

            match data[0]:
                case 1:
                    self.send_videofeed(data)
                    continue
                case 2:
                    self.respond(data)
                    continue
                case 3:
                    self.state(data)
                    continue
                case 4:
                    self.bandwidth_test(data)
                    continue

            message = data.decode()

            if message.startswith("SERVER"):
                self.handle_server_messages(message)
                continue
            if message.startswith("HOLE") and not self.hole_punched:
                self.handle_hole_punch_message()
                continue

            print("Unhandled command/message:", message)

    def main(self) -> None:
        self.register()
        self._run_in_thread(self.listen)
