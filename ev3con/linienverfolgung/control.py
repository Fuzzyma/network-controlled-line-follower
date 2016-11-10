# from ev3.lego import *
# from ev3.ev3dev import NoSuchMotorError, NoSuchSensorError
from ev3dev.ev3 import ColorSensor, LargeMotor
# from multiprocessing import Process, Value
from .pid import PID, RunningAverage

'''
class DistKeep(UltrasonicSensor):
    """Berechnet die noetige Aenderung der Geschwindigkeit(dv) um einen konkreten Abstand(soll) einzuhalten"""
    def __init__(self, soll, port_us, kp, ki=0, kd=0, max_dist=2550, **kwargs):
        """
        INIT-Argumente:
        soll: gewollter Abstand
        kp: Proportionalkonstante 
        ki: Integralkonstante (default = 0)
        kd: Differentialkonstante (default = 0)
        port_us: Port des Ultraschallsensors(default=-1 -> Autodetect)
        max_dist: Entfernungen ueber diesem Wert werden ignoriert!(Default: 2550)
         """
        self.soll = soll
        # print(kwargs)
        self.pid = PID(kp, ki, kd, **kwargs)
        self.max_dist = max_dist
        self.over_max_dist = False
        UltrasonicSensor.__init__(self, int(port_us))

    @property
    def dv(self):
        """noetige Geschwindigkeitsaenderung"""
        ist = self.dist_cm
        if ist>self.max_dist or ist<-self.max_dist: 
            self.over_max_dist = True
            return 0
        else: 
            self.over_max_dist = False
        speed = self.pid.calc(ist, self.soll)
        return int(speed)

    def set_pid(self, **kwargs):
        """PID-Regler einstellen
        Argumente(sh PID): ki, kp, kd, antiwindup, avgsize_d """
        for k in kwargs:
            v = kwargs[k]
            if (v != None):
                setattr(self.pid, k, v)
'''


class BetterColorSensor(ColorSensor):
    """Erweitert die Attribute des Farbsensors"""
    def __init__(self, port=None, avgsize_c=1):
        ColorSensor.__init__(self, address=(port if port is None else str(port)))
        self.avg_r = RunningAverage(avgsize_c)
        self.avg_g = RunningAverage(avgsize_c)
        self.avg_b = RunningAverage(avgsize_c)
        self._avgsize_c = avgsize_c
        self.mode = 'RGB-RAW'

    @property
    def grey(self):
        """gibt den Grauwert aus"""
        return sum((self.value(0), self.value(1), self.value(2)))/3

    '''
    @property
    def color_str(self):
        """gibt die Farbe als String zurueck nicht als int"""
        return self.colors(self.color)
    '''

    @property
    def avgsize_c(self):
        """Anzahl der zu mittelnden Messwerte"""
        return self._avgsize_c

    @avgsize_c.setter
    def avgsize_c(self, size):
        self._avgsize_c = int(size)
        self.avg_r = RunningAverage(size)
        self.avg_g = RunningAverage(size)
        self.avg_b = RunningAverage(size)

    @property
    def rgb_avg(self):
        """mittlere RGB"""
        avg_r = self.avg_r.calc(self.value(0))
        avg_g = self.avg_g.calc(self.value(1))
        avg_b = self.avg_b.calc(self.value(2))
        return avg_r, avg_g, avg_b

    @property
    def grey_avg(self):
        """mittleren Grauwert"""
        return sum(self.rgb_avg)/3


class LineKeep(BetterColorSensor):
    """Berechnet die noetige Aenderung der Geschwindigkeit(dv) um auf der Linie zu bleiben
    TODO:Um die PID-Parameter bei sich aendernden Bedingungen gleich zuhalten, wird der soll und ist-Wert  
    auf 0...255 gemappt
    """
    def __init__(self, port_cs, kp, ki=0, kd=0, avgsize_c=1, white=255, black=0, **kwargs):
        """
        INIT-PARAM:
        kp, ki, kd:Konstanten des PID-Reglers
        port_cs:Port des FarbSensors
        avgsize_c: zu mittelnde Farbwerte( koennte sinnvoll sein wg Schwankungen, default = 1)
        white: Farbe des Untergrunds(default:255)
        black: Farbe der Linie(default:0)
        """
        self._pid = PID(kp, ki, kd, **kwargs)
        BetterColorSensor.__init__(self, port_cs)
        self.grey_soll = ((127.5 - black) / (white - black)) * 255
        self.avgsize_c = avgsize_c
        self.black = black
        self.white = white
    
    @property
    def dv(self):
        """noetige Geschwindigkeitsaenderung"""
        
        if self.avgsize_c > 1:
            grey = self.grey_avg
        else:
            grey = self.grey
        grey = ((grey - self.black) / (self.white - self.black)) * 255
        speed = self._pid.calc(grey, self.grey_soll)

        return int(speed)
    
    def set_pid(self, **kwargs):
        """PID-Regler einstellen
        Argumente(sh PID): ki, kp, kd, antiwindup, avgsize_c """
        for k in kwargs:
            v = kwargs[k]
            if v is not None:
                setattr(self._pid, k, v)

    
class MotorControl(object):
    """Klasse zum Verbinden und Ansteueren mehrere Motoren gleichzeitg
    
    Attribute:
    margin: Maximalwert Geschwindigkeit (mit Speedregulation)
    motors: Dictionary mit den jeweiligen Motoren(value) und Ports(key)
    """
    def __init__(self, avg_speed, inverted=False, **kwargs):
        """INIT-Argument:
            avg_speed: Mittlere Geschwindigkeit an den Motoren
            inverted: falls die Motoren sich anders herum drehen sollen
            
            zusaetzliche Keywordargumente der Motoren sh ev3dev Dokumentation
        """

        self.avg_speed = avg_speed
        self.margin = 1000
        self.motors = {}
        self.inverted = inverted

        self.attach_motors()

    def set_speed(self, speed, ports='ABCD'):
        """setzt eine Geschwindigkeit(additiv zur mittleren) und schreibt den Wert an bestimmte/alle Motoren
        
        Keyword Argumente:
        sp = zu setzende Geschwindigkeit
        ports= Portliste/string der anzusteuernden Motoren
        """

        speed += self.avg_speed
        if self.inverted:
            speed = -speed

        if speed > self.margin:
            speed = self.margin
        elif speed < -self.margin:
            speed = self.margin

        for p in ports:
            if self.motors[p].connected:
                self.motors[p].run_forever(speed_sp=speed, speed_regulation=True)
            else:
                print("Cant run motor on", p, "- not connected")

    def attach_motors(self):
        """Motoren an allen  Ports finden"""
        self.motors = {}
        for port in 'ABCD':
            self.motors[port] = LargeMotor('out' + port)
            if not self.motors[port].connected:
                print("No Motor at port", port)

    def stop(self, ports='ABCD'):
        """Stopt alle Motoren
        
        Keyword Argument:
        ports= Portliste/string der anzusteuernden Motoren
        """

        for p in ports:
            if self.motors[p].connected:
                self.motors[p].stop()

    def reset(self, ports='ABCD'):
        """Resetet alle Motoren

        Keyword Argument:
        ports= Portliste/string der anzusteuernden Motoren
        """

        for p in ports:
            if self.motors[p].connected:
                self.motors[p].reset()

'''
class TotalControl(MotorControl):
    """Kontrolliert die Geschwindigkeit der einzelnen Motoren um einen Abstand und die Linie zu halten.
    Erweitert MotorControl
    """

    def __init__(self, dist_set, line_set, left_ports, right_ports, avg_stop, margin_stop, **kwargs):
                
        MotorControl.__init__(self, **kwargs)
        self.left = left_ports
        self.right = right_ports
        self.line = LineKeep(**line_set)
        self.dist = DistKeep(**dist_set)
        self.stopped = Value('b',True)
        self.clearpath = Value('b',True)
        self.margin_stop = margin_stop
        self.avg = RunningAverage(avg_stop, self.avg_speed)
        self.process = Process(target=self.run)
        
    def start(self, idle = False):
        
        if idle:
            self.process = Process(target=self.run_idle)
        else:  
            self.stopped = False
            self.process = Process(target=self.run)
        self.process.start()
        
    def stop(self):
        self.stopped = True
        self.stop_motors()
        self.process.terminate()
        
    def run(self):
        while True:
            dv_d = self.dist.dv
            dv_l = self.line.dv
            dv_left = -dv_d - dv_l 
            dv_right = -dv_d + dv_l

            avg = abs(self.avg.calc(dv_d) - self.avg_speed)
            under_margin = avg < self.margin_stop and not self.dist.over_max_dist
            if under_margin: 
                self.stop_motors()
                self.stopped = True
                self.clearpath = False
                break
            else:
                self.set_speed(dv_left, self.left)
                self.set_speed(dv_right, self.right)
                
    def run_idle(self):
        while True:
            dv_d = self.dist.dv
            avg = abs(self.avg.calc(dv_d) - self.avg_speed)
            under_margin = avg < self.margin_stop and not self.dist.over_max_dist
            if not under_margin: 
                self.clearpath = True
                break
'''
