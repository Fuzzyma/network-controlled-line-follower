#!/usr/bin/env python3

from ev3dev.ev3 import LargeMotor
import sys
import time

try:
    ports = sys.argv[1]
except IndexError:
    ports = 'ABCD'

motors = {}

for i in ports:
    port = "out" + i
    temp = LargeMotor(address=port)
    if temp.connected:
        motors[i] = temp


print("running measurements...")

for i in motors:
    port = "out" + i
    print("Measure motor at port", port)
    start = time.time()
    for cnt in range(1000):
        motors[i].run_forever(speed_sp=cnt, speed_regulation=True)
    end = time.time()
    print("Motor", port, "needed", (end-start), "ms in average")


print("Measure all motors together")

start = time.time()

for cnt in range(1000):
    for i in motors:
        motors[i].run_direct(speed_sp=cnt)
end = time.time()

print("Motors needed", (end-start), "ms in average")