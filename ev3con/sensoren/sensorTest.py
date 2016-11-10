# -*- coding: utf-8 -*-
"""
Created on Wed Jul  8 08:27:39 2015

@author: lukas
"""

from ev3.ev3dev import *
from ev3.lego import *
import time

def sensorTest():
    print(time.time())
    counter = 0
    us = UltrasonicSensor()
    ttemp= 0
    while counter < 1000:
        t1 = us.dist_cm
        if t1 != ttemp:
            counter +=1
            t1 = ttemp
    print(time.time())
        