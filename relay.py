from stun.relay_stun_client import RelayStunClient

client = RelayStunClient()
client.relay = True
# Response from drone to the relay but not to the operator
client.drone_command_socket.bind(("0.0.0.0", 9000))
client.main()
client.run_in_thread(client.state_socket_handler)

seq_num = 0

while client.running:
    if client.hole_punched:
        seq_byte = seq_num.to_bytes(2, 'big')

        msg = client.drone_video_socket.recv(4096)
        client.send_data_to_operator(seq_byte + msg)
        #print(f"From relay: {seq_num}")
        seq_num = (seq_num + 1) % 65536
