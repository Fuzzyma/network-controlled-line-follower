#!/usr/bin/env python3

import socket
import time
import string
import random
import select
from node.constants import BOT_ADDR, AP_ADDR

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(BOT_ADDR)

# Use non blocking methods (program flow will not get interrupted)
sock.setblocking(True)

print("running measurements...")

msgs = []

for d in range(1000):
    msgs[d] = ''.join(random.choice(string.ascii_uppercase) for _ in range(50))

start = time.time()
while d in msgs:
    sock.sendto(d.encode('utf-8'), AP_ADDR)
end = time.time()

print("Socket needed", (end-start), "ms in average to send a message")

readable, writable, exceptional = select.select([sock], [], [sock], 0)

if not readable:
    return False

try:
    payload, addr = sock.recvfrom(256)
except (socket.error, socket.herror, socket.gaierror, socket.timeout):
    return False
else:
    received = json.loads(payload.decode("utf-8"))