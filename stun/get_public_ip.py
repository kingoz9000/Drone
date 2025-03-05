import stun

nat_type, external_ip, external_port = stun.get_ip_info(stun_host="130.225.37.157", stun_port=3478)

print(f"Detected NAT Type: {nat_type}")
print(f"Public IP: {external_ip}")
print(f"Public Port: {external_port}")

