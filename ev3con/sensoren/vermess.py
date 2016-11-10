# -*- coding: utf-8 -*-
"""
Created on Mon Jun  1 19:34:44 2015

@author: lukas
"""
import datetime
from ev3.ev3dev import Key, Tone
from ev3.lego import UltrasonicSensor
#import unittest
#from util import get_input
#import time

class superSonicTest:
    
    s = UltrasonicSensor()
    key=Key()
#    tone=Tone()
    distmax=150
    dist= 0        
#    tone.play(1000, 3000)
  #  time.sleep(0.01)
 #   tone.stop()    
    
    while True:
            if key.up:        
                break 
            dist=s.dist_cm
            time=datetime.datetime.now()    
            print(dist)
            print(time)
 #           if s.dist_cm<distmax:
 #               tone.play(1000, 3000)
 #               time.sleep(0.1)
 #               tone.stop() 
    