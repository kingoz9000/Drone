import heapq
import time
from queue import Queue

from .stun_client import StunClient


class ControlStunClient(StunClient):
    def __init__(self, log):
        super().__init__()
        self.response = Queue()
        self.log = log
        self.data_file_name = (
            f"{time.strftime('%Y-%m-%d_%H-%M-%S', time.localtime())}seq.txt"
        )
        self.reorder_buffer: list[tuple] = []
        self.MIN_BUFFER_SIZE = 6
        self.last_seq_num = 0

    def send_command_to_relay(self, command, print_command=False, take_response=False):
        self.stun_socket.sendto(command.encode(), self.peer_addr)

    def get_peer_addr(self):
        if self.peer_addr:
            return self.peer_addr

    def listen(self):
        # video_file = open("output_stream.h264", "ab")  # append in binary mode
        while self.running:
            data = self.stun_socket.recv(4096)
            if not self.relay and self.hole_punched:
                flag = data[0]
                self.handle_flags(flag, data)

            message = data.decode()

            if message.startswith("SERVER"):
                self.handle_server_messages(message)

            if message.startswith("HOLE") and not self.hole_punched:
                self.hole_punched = True
                print("Hole punched!")
                self.stun_socket.sendto(b"HOLE PUNCHED", self.STUN_SERVER_ADDR)

            if message.startswith("PEER"):
                # intended for the relay
                continue
            print(f"Received message: {message}")

    def handle_flags(self, flag, data):
        if flag == 0:
            self.reorder_video_packets(data)

        # Response
        elif flag == 1:
            # Skal sendes til TKinter
            self.response.put(data[1:])

        # State
        elif flag == 2:
            self.state = data[1:]

    def reorder_video_packets(self, data):
        seq_num = int.from_bytes(data[1:3], "big")
        payload = data[3:]
        if self.log:
            with open("Data/" + self.file_name, "a") as writer:
                writer.write(f"{seq_num}, {time.perf_counter_ns() // 1_000_000}\n")
        heapq.heappush(self.reorder_buffer, (self, payload))

        if len(self.reorder_buffer) >= self.MIN_BUFFER_SIZE:
            ordered_seq, ordered_data = heapq.heappop(self.reorder_buffer)

            if ordered_seq != self.last_seq_num + 1:
                print(f"Expected: {self.last_seq_num + 1}, Got: {ordered_seq}")

            self.stun_socket.sendto(ordered_data, ("127.0.0.1", 27463))
            # video_file.write(ordered_data)
            self.last_seq_num = ordered_seq
