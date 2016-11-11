from ConfigParser import ConfigParser, NoOptionError
from ev3.ev3dev import Key, Lcd
from PIL import Image,ImageDraw,ImageFont
from control import BetterColorSensor
import time
import os

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
		l=Lcd()
		l.reset()
		font = ImageFont.load_default()
		k=Key()
		c=BetterColorSensor()
		l.draw.text((50, 10), "KALIBRIERUNG", font=font)
		l.draw.text((10, 50), "Farbsensor auf schwarze Linie richten", font=font)
		l.draw.text((10, 70), "weiter mit nach-oben Taste!") 
		while(True):
			l.update()
			black=c.grey
			print('Schwarz:'+str(black))
			if k.up:break
		time.sleep(1)
		l.reset()
		l.draw.text((50, 10), "KALIBRIERUNG", font=font)
		l.draw.text((10, 50), "Farbsensor NEBEN schwarze Linie richten", font=font)
		l.draw.text((10, 70), "weiter mit nach-oben Taste!")
		while(True):
			l.update()
			white=c.grey
			print('Weiss:'+str(white))
			if k.up:break
		l.reset()	
		self.set('Line','white',str(white))
		self.set('Line','black',str(black))
		self.set('Init','calibrate',str(False))
		os.remove(self.path)
		with open(self.path, 'wb') as configfile:
			self.write(configfile)
