import unittest
from control import *
from ev3.ev3dev import Key, Lcd
from PIL import Image,ImageDraw,ImageFont
from configurator import *
#from util import get_input

class TestOr(unittest.TestCase):
	def test_dist(self):
		print('TEST:ABSTAND HALTEN')
		k=Key()
		l=Lcd()
		#~ raw_input('Linker Motor an A, rechter an B?')
		font = ImageFont.load_default()
		
		#~ m=MotorControl(left+right)
		#~ port_us=raw_input('Port Ultraschallsensor?')
		#~ if not port_cs in'1234': port_cs=None
		#~ kp=float(raw_input('KP?\n'))
		#~ ki=float(raw_input('KI?\n'))
		#~ kd=float(raw_input('KD?\n'))
		#~ soll=kd=float(raw_input('Abstand(cm)?\n'))
		#~ dist=DistKeep(soll,kp,ki,kd,port_us,antiwindup=100)
		c=Configurator('ev3.cfg')
		print('USB-Kabel entfernen und RECHTS neben die Linie setzen,sh EV3-Display!')
		param_d=c.config_dist()
		param_m=c.config_motors()
		l.draw.text((10, 10), "Test: Abstand halten  ", font=font)
		l.draw.text((10, 50), "Start:Nach oben Taste", font=font)
		l.draw.text((10, 90), "Ende : Nach untenTaste", font=font)
		l.update()
		while(True):
			l.update()
			if k.up:break
		m=MotorControl(**param_m)
		dist=DistKeep(**param_d)
		while(True):
			if k.down:
				l.draw.text((10, 10), "Test beendet  ", font=font)
				m.stop_motors()
				l.update()
				break
			dv=dist.dv
			
			l.reset()
			l.draw.text((10, 10), "delta_v:", font=font)
			l.draw.text((10, 30), str(dv), font=font)
			l.update()
		
			m.set_speed(-dv)
if __name__ == '__main__':
	unittest.main()

