import socket
import struct

BUFFER_SIZE = 4096

recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
recv_sock.bind(("", 45454))

send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
send_sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 10)
SEND_ADDR = ("224.1.1.1", 54545)

mreq = struct.pack("4sl", socket.inet_aton(SEND_ADDR[0]), socket.INADDR_ANY)
send_sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)


while True:
    data = recv_sock.recv(BUFFER_SIZE)
    send_sock.sendto(data, SEND_ADDR)
