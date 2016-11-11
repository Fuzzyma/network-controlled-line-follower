import unittest
from control import *
from ev3.ev3dev import Key, Lcd
from PIL import Image,ImageDraw,ImageFont
from configurator import *
import time
#from util import get_input

class TestOr(unittest.TestCase):
	def test_line(self):
		print('TEST: LINIE FOLGEN')
		#~ raw_input('Linker Motor an A, rechter an B,Farbsensor an 4?')
		#~ left='A'
		#~ right='B'
		font = ImageFont.load_default()
		#~ #m=MotorControl(right) 
		#~ m=MotorControl(left+right)
		#~ #m.inverted=True
		#~ m_avg_speed=int(raw_input('Mittlere Geschwindigkeit der Motoren\n'))
		#~ print(type(m_avg_speed))
		#~ kp=float(raw_input('KP?\n'))
		#~ ki=float(raw_input('KI?\n'))
		#~ kd=float(raw_input('KD?\n'))
		#~ avg=int(raw_input('Wie viele Farbwerte mitteln?\n'))
		c=Configurator('ev3.cfg')
		if raw_input('Kalibrierung? y/n')=='y':
			c.calibrate_line()
		print('USB-Kabel entfernen und RECHTS neben die Linie setzen,sh EV3-Display!')
		param_l=c.config_line()
		param_m=c.config_motors()
		left=param_m['left_ports']
		right=param_m['right_ports']
		print(param_m)
		#~ print(m.inverted)
		#~ print(m.avg_speed)
		k=Key()
		l=Lcd()
		l.draw.text((10, 10), "Test: Linie folgen  ", font=font)
		l.draw.text((10, 50), "Start:Nach oben Taste", font=font)
		l.draw.text((10, 90), "Ende : Nach untenTaste", font=font)
		while(True):
			l.update()
			if k.up:break
		#~ m.avg_speed=m_avg_speed
		line=LineKeep(**param_l)
		m=MotorControl(**param_m)
		t_old=0
		while(True):
			if k.down:
				l.draw.text((10, 10), "Test beendet  ", font=font)
				m.stop_motors()
				l.update()
				break
			dv=line.dv
			print(dv)
			t=time.time()
			print t-t_old
			t_old=t
			m.set_speed(dv,left)
			m.set_speed(-dv,right)
if __name__ == '__main__':
	unittest.main()

