#!/usr/bin/env python3

import time
from node.MotorControl import MotorControl


control = MotorControl("AD")

print("running measurements...")

for i in "AD":
    port = "out" + i
    print("Measure motor at port", port)
    start = time.time()
    for cnt in range(2000):
        control.set_speed(cnt-1000, ports=i)
    control.set_speed(0, ports=i)
    end = time.time()
    print("Motor", port, "needed", (end-start)/2, "ms in average")


print("Measure all motors together")

start = time.time()

for cnt in range(2000):
    for i in "AD":
        control.set_speed(cnt - 1000, ports=i)

control.set_speed(0, ports="AD")
end = time.time()

print("Motors needed", (end-start), "ms in average")