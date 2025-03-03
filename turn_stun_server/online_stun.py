import stun

nat_type, external_ip, external_port = stun.get_ip_info(stun_host="stun.l.google.com", stun_port=19302)
print(f"NAT Type: {nat_type}")
print(f"External IP: {external_ip}")
print(f"External Port: {external_port}")

