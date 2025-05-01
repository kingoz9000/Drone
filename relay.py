from stun.relay_stun_client import RelayStunClient

client = RelayStunClient()
client.relay = True
client.drone_command_socket.bind(("0.0.0.0", 9000))
client.main()
client.run_in_thread(client.state_socket_handler)

seq_num = 0

while client.running:
    if client.hole_punched:
        seq_byte = seq_num.to_bytes(3, "big")

        try:
            msg = client.drone_video_socket.recv(4096)
        except KeyboardInterrupt:
            print(" Exiting Relay, BYE!")
            break
        except Exception as e:
            print(e)
            exit(1)
        client.send_data_to_operator(seq_byte + msg)
        seq_num = seq_num + 1
