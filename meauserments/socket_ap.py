#!/usr/bin/env python3

import socket
import time
import string
import random
import select
import sys
import time

sys.path.append("..")

from node.constants import BOT_ADDR, AP_ADDR

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(AP_ADDR)

# Use non blocking methods (program flow will not get interrupted)
sock.setblocking(True)

print("running measurements...")

msgs = []

for d in range(1000):
    msgs.append(''.join(random.choice(string.ascii_uppercase) for _ in range(50)))

while True:
    for d in msgs:
        sock.sendto(d.encode('utf-8'), BOT_ADDR)
        #print(d)
        #time.sleep(0.1)


