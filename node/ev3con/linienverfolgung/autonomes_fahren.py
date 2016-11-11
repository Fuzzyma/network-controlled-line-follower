from ConfigParser import ConfigParser, NoOptionError
from ev3.ev3dev import Key, Lcd
from PIL import Image,ImageDraw,ImageFont
from control import *
import time
import os

key = Key()
lcd = Lcd()
font = ImageFont.load_default()

class Configurator(ConfigParser):
	def __init__(self,path):
		ConfigParser.__init__(self)
		self.path=path
		self.read(path)
	def config_init(self):
		out={}
		for o in self.options('INIT'):
			out[o]=self.getboolean('INIT',o)
		if out['calibrate'] :
			self.calibrate_line()
		return out
	def config_motors(self):
		'''Gibt die Einstellungen fuer die Motoren als Dict zurueck'''
		
		out={}
		for o in self.options('Motors'):
			val=self.get('Motors',o)
			try: 
				val=int(val)
			except:
				pass
			out[o]=val
		return out
	
	def config_dist(self):
		'''Liest die Einstellungen zum Abstand halten aus der Config  und gibt sie als Dict zurueck '''
		out={}
		for o in self.options('Distance'):
			out[o]=self.getfloat('Distance',o)
		out['port_us']=int(out['port_us'])
		return out
		
	
	def config_line(self):
		'''Liest die Einstellungen zum Halten der Linie aus der Config  und gibt sie als Dict zurueck '''
		out={}
		for o in self.options('Line'):
			out[o]=self.getfloat('Line',o)
		out['port_cs']=int(out['port_cs'])
		#~ if 'avgsize' in out:
			#~ out['avgsize']=int(out['avgsize'])
		return out
	def calibrate_line(self):
		c=BetterColorSensor()
		lcd.draw.text((50, 10), "KALIBRIERUNG", font=font)
		lcd.draw.text((10, 50), "Farbsensor auf schwarze Linie richten", font=font)
		lcd.draw.text((10, 70), "weiter mit nach-oben Taste!") 
		while(True):
			lcd.reset()
			black=c.grey
			lcd.draw.text((50, 10), "SCHWARZ", font=font)
			lcd.draw.text((10, 50), str(black), font=font)
			lcd.update()
			if key.up : break
		lcd.reset()
		lcd.draw.text((50, 10), "KALIBRIERUNG", font=font)
		lcd.draw.text((10, 50), "Farbsensor NEBEN schwarze Linie richten", font=font)
		lcd.draw.text((10, 70), "weiter mit nach-oben Taste!")
		while(True):
			if key.up : break
		while(True):
			lcd.reset()
			white=c.grey
			lcd.draw.text((50, 10), "WEISS", font=font)
			lcd.draw.text((10, 50), str(white), font=font)
			lcd.update()
			if key.up : break
		lcd.reset()	
		self.set('Line','white',str(white))
		self.set('Line','black',str(black))
		self.set('INIT','calibrate',str(False))
		os.remove(self.path)
		with open(self.path, 'wb') as configfile:
			self.write(configfile)



	
def main():
	##################CONFIG/CALIBRATION#########################
	
	try:
		conf = Configurator('/home/ev3con/python-ev3con/control/ev3.cfg')
		param_i = conf.config_init()
		param_l = conf.config_line()
		param_d = conf.config_dist()
		param_m = conf.config_motors()
		print(param_i['restart'])
		restart = param_i['restart']
	except:
		lcd.draw.text((10, 10), "Config-File Fehler", font=font)
		lcd.draw.text((10, 50), "Ende : Nach unten Taste", font=font)
		while(True):
			lcd.update()
			if key.down : break
		return 1
		
	############################INIT#########################
	#try:
	control=TotalControl(param_d,param_l,**param_m)
	#Weitere Initialisierungen hier einfuegen
	#except:
	#	lcd.draw.text((10, 10), "Initialisierungs Fehler", font=font)
	#	lcd.draw.text((10, 50), "Ende : Nach unten Taste", font=font)
	#	while(True):
	#		lcd.update()
	#		if key.down : break
	#	return 1
	############################START##############################
	lcd.draw.text((10, 10), "Start : Nach unten Taste", font=font)
	while(True):
		lcd.update()
		if key.down : break
	time.sleep(1)
	control.start()
	############################MAINLOOP############################
	while(True):
		
		if control.stopped and restart:
			control.start(idle=True)
			if control.clearpath:
				control.start()
		if key.down:
			print('Stop')
			break
	############################ENDE########################
	control.stop()
	lcd.draw.text((10, 10), "Beendet  ", font=font)
	lcd.update()
	return 0

if __name__ == '__main__':
	main()



