import sys, time, traceback, argparse
from ev3.ev3dev import *
from ev3.lego import *

import sys, argparse, socket
from multiprocessing import Process
from ev3.ev3dev import Motor

class PID:
    def __init__(self, Kp=0.0, Ki=0.0, Kd=0.0):
        self.reset(Kp, Ki, Kd)

    def reset(self, Kp=0.0, Ki=0.0, Kd=0.0):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.lasterror = 0.0
        self.integral = 0.0
        self.derivative = 0.0
        self.correction = 0.0

    def calc(self, error, limit=None):
        self.integral = 0.5 * self.integral + error
        self.derivative = error - self.lasterror
        self.lasterror = error
        self.correction = self.Kp * error + self.Ki * self.integral + self.Kd * self.derivative

        if not limit == None:
            if abs(self.correction) > abs(limit):
                self.correction = (self.correction / abs(self.correction)) * limit

        return self.correction

def follow_line(Vref=0.0, colmax=0.0, colmin=0.0, distref=0.0, lKp=0.0, lKi=0.0, lKd=0.0, dKp=0.0, dKi=0.0, dKd=0.0):
    cycle_t = 0.0
    standing_t = 0.0
    pid_line = PID(lKp, lKi, lKd)
    pid_dist = PID(dKp, dKi, dKd)

    ml = Motor(port=Motor.PORT.A)
    mr = Motor(port=Motor.PORT.B)

    cs = ColorSensor()
    us = UltrasonicSensor()
    hupe = Tone()

    led = LED()
    led.left.color = LED.COLOR.AMBER
    led.right.color = LED.COLOR.AMBER

    try:
        ml.run_forever(Vref, speed_regulation=True)
        mr.run_forever(Vref, speed_regulation=True)

        while True:
            cycle_t = time.time()

            # die Farbwerte werden automatisch auf Bereich [0,100] abgebildet, Differenz zu 50 ist Fehler fuer PID
            pid_line.calc( 50 - ( ( cs.reflect - colmin ) / ( colmax - colmin ) ) * 100 )
            pid_dist.calc( distref - us.dist_cm )

            # es soll nicht auf Hindernis zubeschleunigt werden
            if pid_dist.correction < 0:
                pid_dist.correction = 0

            # Motoren werden invertiert angesteuert, da sie in anderer Richtung verbaut sind
            if pid_line.correction > 0: # im dunklen Bereich
                ml.run_forever( (-1) * ( Vref - pid_dist.correction ) )
                mr.run_forever( (-1) * ( Vref - pid_dist.correction - pid_line.correction ) )
            elif pid_line.correction < 0: # im hellen Bereich
                ml.run_forever( (-1) * ( Vref - pid_dist.correction + pid_line.correction ) )
                mr.run_forever( (-1) * ( Vref - pid_dist.correction ) )

            # Startzeit des Zuckelns merken
            if abs( Vref - pid_dist.correction ) < 100 and not standing_t:
                standing_t = time.time()

            if abs( Vref - pid_dist.correction ) > 100 and standing_t:
                standing_t = 0

            # Fahrtsteuerung komplett abschalten, wenn mind. 1 Sekunde gezuckelt wurde
            if standing_t and ( time.time() - standing_t ) > 1:
                ml.stop()
                mr.stop()
                led.left.color = LED.COLOR.RED
                led.right.color = LED.COLOR.RED
                hupe.play(100,500)
                return

            print "Zyklusdauer: " + str( ( time.time() - cycle_t ) * 1000 ) + "ms"

    except:
        ml.stop()
        mr.stop()

        print traceback.format_exc()
        print "Programm wurde beendet"

def wait_barrier(distref=0.0):
    us = UltrasonicSensor()

    while True:
        if us.dist_cm > distref:
            return

        time.sleep(0.03)

import socket, re, time, select

class message(object):
    def __init__(self,typ ,ID,target, timestamp, msg):
        self.typ = typ
        self.ID = ID
        self.timestamp = timestamp
        self.msg = msg
        self.target = target
    # Objektvorlage um Nachrichten zu speichern um sie ggf. zu wiederholen

class comUTP(object):
    def __init__(self, position, length):
        #Globale Variablen
        self.interface = []
        self.sendeflag = 1
        self.RECV_BUFFER = 4096 # Advisable to keep it as an exponent of 2
        self.buff = ''
        self.counter = 0 # Notwendig fur eindeutiges Datum der ID        
        self.PORT = 5000
        #Klassenvariablen 
        self.zaehler= 0
        self.position = int(position)
        self.length = int(length)
        self.listIPs = ['10.255.255.255','10.42.1.11','10.42.1.14','10.42.1.15','10.42.1.16','10.42.1.17','10.42.1.15']
        self.check_list = []        #,'10.42.1.12','10.42.1.13'
        #Initialisiere ListenSocket
        self.ownIP = self.listIPs[self.position]
        '''
        Erstelle  bzw. binde die Sockets.
        1 Socket fuer eingehende Nachricht.
        2 Sockets fuer Fahrzeuge vor und hinter Teilnehmer.
        '''
        try:
            self.rec_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        except socket.error:
            print('Check1')
        try:
            self.rec_sock.bind(('0.0.0.0',self.PORT))
        except socket.error:
            print('Check2')
            
        #self.rec_sock = socket.setdefaulttimeout(100.05)
        
        try:
            self.send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        except socket.error:
            print('Check3')
        
        self.rec_sock.setblocking(0)
        self.send_sock.setsockopt(socket.SOL_SOCKET,socket.SO_BROADCAST,1)
    def check(self):
       
        try:
            while True:
                data= self.rec_sock.recvfrom(self.RECV_BUFFER)
                print(data)
                self.decode(data[0])
        except (socket.error, socket.timeout, AttributeError):
            pass
        if len(self.check_list)>0:
            prooftime = time.time()
            del_list = []
            for everyMessage in range(len(self.check_list)):
                if prooftime - self.check_list[everyMessage].timestamp< 0.5:
                    break
                else:
                    self.send(self.check_list[everyMessage].typ,self.check_list[everyMessage].target, self.check_list[everyMessage].msg, self.check_list[everyMessage].ID)
                    del_list.append(everyMessage)#Vorsicht? 
            try:                
                del self.check_list[del_list[0]:len(self.check_list)]
            except:
                pass                
            #continue
            
    def decode(self, dataString=""):
        '''
        Zerlegt Nachricht in Unterteile und uebergibt es msgToHandle
        '''
        rule = r"ANFANG.*?ENDE"
        self.buff += dataString[:]
        try:
            message = re.search(rule, self.buff).group()
        except AttributeError:
            return
        self.buff = re.sub(rule,'',self.buff,1)
        message = re.split(';',message)
        print(message)
        self.handleMsg(message)
        self.decode()
        
    def handleMsg(self,msgToHandle):
        
        msgToHandle[2]= int(msgToHandle[2])
        msgToHandle[3]= int(msgToHandle[3])
        print('handling')
        print(msgToHandle)
        print(msgToHandle[-2])
        if msgToHandle[1] == 'ACK':
            print('ACK erhalten')
            checkID = msgToHandle[4]
            print(checkID)
            for everyMessage in self.check_list:
                if checkID == everyMessage.ID:
                    print('Gefunden')
                    try:
                        self.check_list.remove(everyMessage)
                    except:
                        print('ACKERN')
                    print('ACK erhalten und entfernt')
                    return# Wenn ACK empfangen wude muss lediglich die Notiz entfernt werden. Danach breche ab.
        if msgToHandle[1] == 'broadcast':
            print(msgToHandle[1])
            self.do(msgToHandle[-2])
            return
        if msgToHandle[1] == 'direct':
            print(msgToHandle[-2])
            self.send('ACK',msgToHandle[3],' ' , msgToHandle[4])
            self.do(msgToHandle[-2])
        if msgToHandle[1] == 'hopbyhop_alle':
            if (self.position>1) and (self.position<self.length):
                self.send(msgToHandle[1],self.position+msgToHandle[3]-msgToHandle[2])
            self.send('ACK',msgToHandle[3],' ' , msgToHandle[4])
            self.do(msgToHandle[-2])
        if msgToHandle[1] == 'hopbyhop_ziel':
            if (self.position!= int(msgToHandle[5])) and (self.position>1) and (self.position<self.length):
                self.send(msgToHandle[1],self.position+msgToHandle[2]-msgToHandle[3])
                self.send('ACK',msgToHandle[3],' ' , msgToHandle[4])
                return
            else:
                self.do(msgToHandle[-2])
                self.send('ACK',msgToHandle[3],' ' , msgToHandle[4])                
                
    def do(self,order):
        self.interface.append(order)
        
        if order == 'timecheck': 
            print('Timecheck')
            if self.position == self.length:
                self.send('hopbyhop_alle', self.position-1, 'timecheck')
            if self.position == 1:
                self.zaehler+=1
                self.sendeflag = 1
    '''
    def timetest(self):
        self.zaehler = 0
        print(time.time())
        while self.zaehler < 10000:
            self.check()
            if self.sendeflag == 1:
                self.send('hopbyhop_all', 2, 'timecheck')
            self.sendeflag = 0
        print(time.time())
       ''' 
    def send(self,typ,target, nachricht, ID=' '):
        
        if ID == ' ':
            self.counter+= 1
            ID = self.ownIP +'.' +str(self.counter)
            self.check_list.append(message(typ,ID,target,time.time(), nachricht))            
        NACHRICHT = "ANFANG;" + typ + ';' + str(target)+ ";" + str(self.position) + ";" + str(ID) + ";" + str(nachricht) + ";ENDE"        
        self.send_sock.sendto(NACHRICHT,(self.listIPs[target],self.PORT))
        print'Sende'
        print NACHRICHT

    def send_halt(self,nachricht):
        self.send('hopbyhop_alle',self.position+1, nachricht)
        
    def broadcast(self,nachricht):
        self.send('broadcast',0,nachricht,'IrgendeineID')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(sys.argv[0])
    parser.add_argument('-Vref', dest='Vref', type=float, default=350)
    parser.add_argument('-colmax', dest='colmax', type=float, default=63.0)
    parser.add_argument('-colmin', dest='colmin', type=float, default=7.0)
    parser.add_argument('-distref', dest='distref', type=float, default=30.0) # Abstand in cm
    parser.add_argument('-lKp', dest='lKp', type=float, default=3.5)
    parser.add_argument('-lKi', dest='lKi', type=float, default=0.0)
    parser.add_argument('-lKd', dest='lKd', type=float, default=2.0)
    parser.add_argument('-dKp', dest='dKp', type=float, default=30.0)
    parser.add_argument('-dKi', dest='dKi', type=float, default=0.0)
    parser.add_argument('-dKd', dest='dKd', type=float, default=0.0)
    args = parser.parse_args(sys.argv[1:])
        
    com = comUTP(2,2)
    p = Process( target=follow_line, args=[args.Vref, args.colmax, args.colmin, args.distref, args.lKp, args.lKi, args.lKd, args.dKp, args.dKi, args.dKd] )
    c = Process( target = wait_barrier, args =[14])
    while True:
        p = Process( target=follow_line, args=[args.Vref, args.colmax, args.colmin, args.distref, args.lKp, args.lKi, args.lKd, args.dKp, args.dKi, args.dKd] )
        p.start()       
        while True:#Waehrend wir fahren
            com.check()
            for alle in com.interface:
                if alle == 'Stop':
                    p.terminate()
                    break
            com.interface = []
            
            if not p.is_alive():
                print'psdead'
                print (com.position)
                if com.position == 1:
                    com.send('direct',1,'Stop')
                break
        c = Process( target = wait_barrier, args =[50])
        c.start()
        while True:#Listening
            com.check()
            for alle in com.interface:
                if alle == 'Start':
                    break
            com.interface = []
            if com.position == 1 and not c.is_alive():
                com.send('direct', com.position+1, 'Start')
                break
            
    