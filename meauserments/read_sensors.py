#!/usr/bin/env python3

from ev3dev.ev3 import ColorSensor
import sys
import time

try:
    ports = sys.argv[1]
except IndexError:
    ports = '1234'

sensors = {}

for i in ports:
    port = "in" + i
    temp = ColorSensor(address=port)
    if temp.connected:
        temp.mode = ColorSensor.MODE_RGB_RAW
        sensors[i] = temp


print("running measurements...")

for i in sensors:
    port = "in" + i
    print("Measure port", port)
    start = time.time()
    for cnt in range(1000):
        r = sensors[i].value(0)
        g = sensors[i].value(1)
        b = sensors[i].value(2)
    end = time.time()
    print("Sensor", port, "needed", (end-start), "ms in average")


print("Measure all ports together")

start = time.time()

for cnt in range(1000):
    for i in sensors:
        r = sensors[i].value(0)
        g = sensors[i].value(1)
        b = sensors[i].value(2)
end = time.time()

print("Sensor", i, "needed", (end-start), "ms in average")
