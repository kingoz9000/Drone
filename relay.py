from stun.relay_stun_client import RelayStunClient
import hashlib
from main import args


client = RelayStunClient(args.log)
client.relay = True
# Response from drone to the relay but not to the operator
client.drone_command_socket.bind(("0.0.0.0", 9000))
client.main()
client.run_in_thread(client.state_socket_handler)

seq_num = 0

while client.running:
    if client.hole_punched:
        seq_byte = seq_num.to_bytes(2, "big")
        msg = client.drone_video_socket.recv(4096)
        checksum = hashlib.md5(msg).digest()[:4]  # adds checksum to the message
        client.send_data_to_operator(seq_byte + msg + checksum)

        # Log the checksum with sequence number and timestamp
        if args.log:
            with open("Data/relay_checksums.log", "a") as relay_check:
                relay_check.write(
                    f"Seq: {seq_num}, Checksum: {checksum.hex()}, Message Size: {len(msg)} bytes\n"
                )

        seq_num = (seq_num + 1) % 65536
