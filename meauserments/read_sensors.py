#!/usr/bin/env python3

from ev3dev.ev3 import ColorSensor
import sys
import time

try:
    ports = sys.argv[0]
except IndexError:
    ports = '1234'

sensors = {}

for i in ports:
    temp = ColorSensor(address=i)
    if temp.connected:
        temp.mode = 'RGB-RAW'
        sensors[i] = temp


print("running measurements...")

for i in sensors:
    print("Measure port", "in"+i)
    start = time.time()
    for cnt in range(1000):
        r = sensors[i].value(0)
        g = sensors[i].value(1)
        b = sensors[i].value(2)
    end = time.time()
    print("Sensor", i, "needed", (end-start), "ms in average")


print("Measure all ports together")

start = time.time()

for cnt in range(1000):
    for i in sensors:
        r = sensors[i].value(0)
        g = sensors[i].value(1)
        b = sensors[i].value(2)
end = time.time()

print("Sensor", i, "needed", (end-start), "ms in average")
