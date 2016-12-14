#!/usr/bin/env python3

from ev3dev.ev3 import ColorSensor
import sys
import time

sys.path.append("..")

from node.ColorSensor import ColorSensor

try:
    ports = sys.argv[1]
except IndexError:
    ports = '1234'

sensors = {}

for i in ports:
    port = "in" + i
    temp = ColorSensor(port=i, mode=ColorSensor.MODE_COL_REFLECT)
    if temp.connected:
        sensors[i] = temp


print("running measurements...")

for i in sensors:
    port = "in" + i
    print("Measure sensor at port", port)
    start = time.time()
    for cnt in range(1000):
        r = sensors[i].light
    end = time.time()
    print("Sensor", port, "needed", (end-start), "ms in average")


print("Measure all sensors together")

start = time.time()

for cnt in range(1000):
    for i in sensors:
        r = sensors[i].light
end = time.time()

print("Sensors needed", (end-start), "ms in average")
