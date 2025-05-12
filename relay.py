import time  # Add this import for timing
from stun.relay_stun_client import RelayStunClient


class Relay:
    def __init__(self) -> None:
        self.client = RelayStunClient()
        self.client.relay = True
        self.client.drone_command_socket.bind(("0.0.0.0", 9000))
        self.client.main()
        self.client._run_in_thread(self.client.state_socket_handler)
        # self.client._run_in_thread(self.client.bandwidth_tester(1024, 1))

        self.seq_num = 0

    def main(self) -> None:
        start_time = time.time()  # Record the start time
        packet_count = 0  # Initialize packet counter

        while self.client.running:
            if self.client.hole_punched:
                seq_byte = self.seq_num.to_bytes(3, "big")

                try:
                    msg = self.client.drone_video_socket.recv(4096)
                except KeyboardInterrupt:
                    print(" Exiting Relay, BYE!")
                    break
                except Exception as e:
                    print(e)
                    exit(1)

                self.client.send_data_to_operator(seq_byte + msg)
                self.seq_num += 1
                packet_count += 1  # Increment packet counter


if __name__ == "__main__":
    relay = Relay()
    relay.main()
