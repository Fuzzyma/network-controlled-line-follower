from ConfigParser import ConfigParser, NoOptionError
from ev3.ev3dev import Key, Lcd
from PIL import Image,ImageDraw,ImageFont
from control import *
import time
import os
import socket, select, string, sys
from multiprocessing import Queue

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

def communicate(port,host,q):
	#~ host = sys.argv[1]
	#~ port = int(sys.argv[2])
	
	
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.settimeout(2)
	 
	# connect to remote host
	try :
		s.connect((host, port))
	except :
		print 'Unable to connect'
		sys.exit()
	 
	print 'Connected to remote host. Start sending messages'
	#~ prompt()
	 
	while 1:
		socket_list = [sys.stdin, s]
		 
		# Get the list sockets which are readable
		read_sockets, write_sockets, error_sockets = select.select(socket_list , [], [])
		 
		for sock in read_sockets:
			#incoming message from remote server
			if sock == s:
				data = sock.recv(4096)
				if not data :
					print '\nDisconnected from chat server'
					sys.exit()
				else :
					#print data
					#~ "sys.stdout.write(data)
					#~ "prompt()
					try:
						print data
						#commands[str(data)]()
						q.put(data)
					except:
						pass
			 
			#user entered a message
			else :
				"""msg = sys.stdin.readline()
				s.send(msg)
				prompt()"""

def test():
 print "hurra"	
def main():
	##################CONFIG/CALIBRATION#########################
	try:
		conf = Configurator('ev3.cfg')
		param_i = conf.config_init()
		param_l = conf.config_line()
		param_d = conf.config_dist()
		param_m = conf.config_motors()
		#param_comm
	except:
		lcd.draw.text((10, 10), "Config-File Fehler", font=font)
		lcd.draw.text((10, 50), "Ende : Nach unten Taste", font=font)
		while(True):
			lcd.update()
			if key.down : break
		return 1
		
	############################INIT#########################
	q = Queue()
	process_com = Process(target = communicate, args=[5000,'10.42.1.1',q])
	try:
		control=TotalControl(param_d,param_l,**param_m)
		commands = {"stop" : control.stop, "start" : control.start, "test" : test }
		
	#Weitere Initialisierungen hier einfuegen
	except:
		lcd.draw.text((10, 10), "Initialisierungs Fehler", font=font)
		lcd.draw.text((10, 50), "Ende : Nach unten Taste", font=font)
		while(True):
			lcd.update()
			if key.down : break
		return 1
	
	
	############################START##############################
	lcd.draw.text((10, 10), "Start : Nach unten Taste", font=font)
	while(True):
		lcd.update()
		if key.down : break
	time.sleep(1)
	control.start()
	process_com.start()
	############################MAINLOOP############################
	while(True):
		#~ if control.stopped and restart:
			#~ 
			#~ control.start(idle=True)
			#~ if control.clearpath:
				#~ control.start()
		data=str(q.get())
		print "try: " + data
		if data.find("stop") != -1:
			control.stop()
		if data.find("start") != -1:
			control.start()
		try:
			commands[data[1:4]]()
		except:
			pass
		if key.down:
			print('Stop')
			break
	############################ENDE########################
	control.stop()
	process_com.terminate()
	lcd.draw.text((10, 10), "Beendet  ", font=font)
	lcd.update()
	return 0

if __name__ == '__main__':
	main()



