#!/usr/bin/env python3

import socket
import time
import select
import sys

sys.path.append("..")

from node.constants import BOT_ADDR

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(BOT_ADDR)

# Use non blocking methods (program flow will not get interrupted)
sock.setblocking(True)

print("running measurements...")

benchmark = []

while True:
    start = time.time()

    readable, writable, exceptional = select.select([sock], [], [sock], 0)

    if not readable:
        continue

    try:
        payload, addr = sock.recvfrom(256)
    except (socket.error, socket.herror, socket.gaierror, socket.timeout):
        print("exception")
        continue
    else:
        received = payload
        print("got", received)


    end = time.time()

    benchmark.append(end-start)
    if len(benchmark) == 1000:
        break

print("Socket needed", (sum(benchmark)), "ms in average to receive a message")
