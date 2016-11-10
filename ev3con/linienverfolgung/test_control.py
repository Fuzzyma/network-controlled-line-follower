import unittest
from control import *
from ev3.ev3dev import Key, Lcd
from PIL import Image,ImageDraw,ImageFont
from configurator import *
#from util import get_input

class TestOr(unittest.TestCase):
	def test_control(self):
		print('TEST:ABSTAND+Linie HALTEN')
		k=Key()
		l=Lcd()
		font = ImageFont.load_default()
		c=Configurator('ev3.cfg')
		print('USB-Kabel entfernen und RECHTS neben die Linie setzen,sh EV3-Display!')
		param_l=c.config_line()
		param_d=c.config_dist()
		param_m=c.config_motors()
		print(param_m)
		print(param_l)
		print(param_d)
		l.draw.text((10, 10), "Test: Abstand+Linie halten  ", font=font)
		l.draw.text((10, 50), "Start:Nach oben Taste", font=font)
		l.draw.text((10, 90), "Ende : Nach untenTaste", font=font)
		l.update()
		while(True):
			l.update()
			if k.up:break
		cont=TotalControl(param_d,param_l,**param_m)
		
		cont.start()
		while(True):
			if k.down:
				l.draw.text((10, 10), "Test beendet  ", font=font)
				cont.stop()
				l.update()
				print('ENDE')
				break
if __name__ == '__main__':
	unittest.main()
