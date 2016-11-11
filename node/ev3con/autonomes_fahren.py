# autonomes_fahren.py - Automatische Linienverfolung unter Wahrung des Abstandes zum Vordemann oder Hindernis
# 2015-07-20 - Hauptseminar KMS - Lukas Egge, Justus Rischke, Tobias Waurick, Patrick Ziegler - TU Dresden

import sys, time, argparse
from ev3.ev3dev import *
from ev3.lego import *

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

def follow_line(Vref=0.0, colmax=0.0, colmin=0.0, distref=0.0, Vtremble=0.0, timeout=0.0, cycledelay=0.0, lKp=0.0, lKi=0.0, lKd=0.0, dKp=0.0, dKi=0.0, dKd=0.0):
    cycle_t = 0.0
    tremble_t = 0.0

    pid_line = PID(lKp, lKi, lKd)
    pid_dist = PID(dKp, dKi, dKd)

    ml = Motor(port=Motor.PORT.A)
    mr = Motor(port=Motor.PORT.B)

    cs = ColorSensor()
    us = UltrasonicSensor()
    hupe = Tone()

    led = LED()
    led.left.color = LED.COLOR.GREEN
    led.right.color = LED.COLOR.GREEN

    try:
        ml.run_forever((-1) * Vref, speed_regulation=True)
        mr.run_forever((-1) * Vref, speed_regulation=True)

        while True:
            cycle_t = time.time()

            # die Farbwerte werden automatisch auf Bereich [0,100] abgebildet, Differenz zu 50 ist Fehler fuer PID
            pid_line.calc( 50 - ( ( cs.reflect - colmin ) / ( colmax - colmin ) ) * 100 )
            pid_dist.calc( distref - us.dist_cm )

            # es soll nicht auf Hindernis zubeschleunigt werden
            if pid_dist.correction < 0:
                pid_dist.correction = 0

            # Motoren werden invertiert angesteuert, da sie in "falscher" Richtung verbaut sind
            if pid_line.correction > 0: # im dunklen Bereich
                ml.run_forever( (-1) * ( Vref - pid_dist.correction ) )
                mr.run_forever( (-1) * ( Vref - pid_dist.correction - pid_line.correction ) )
            elif pid_line.correction < 0: # im hellen Bereich
                ml.run_forever( (-1) * ( Vref - pid_dist.correction + pid_line.correction ) )
                mr.run_forever( (-1) * ( Vref - pid_dist.correction ) )

            if timeout:
                # Startzeit des Zuckelns merken
                if abs( Vref - pid_dist.correction ) < Vtremble and not tremble_t:
                    tremble_t = time.time()

                if abs( Vref - pid_dist.correction ) > Vtremble and tremble_t:
                    tremble_t = 0

                # Fahrtsteuerung komplett abschalten, wenn mind. <timeout> Sekunden gezuckelt wurde
                if tremble_t and ( time.time() - tremble_t ) > timeout:
                    ml.stop()
                    mr.stop()
                    led.left.color = LED.COLOR.RED
                    led.right.color = LED.COLOR.RED
                    hupe.play(100,500)
                    return

            # Hier wird die Zyklusdauer kuenstlich verlaengert, falls gefordert
            if cycledelay:
                time.sleep(cycledelay)

            print "Regelzyklus: " + str( ( time.time() - cycle_t ) * 1000 ) + "ms"

    except (KeyboardInterrupt, SystemExit):
        ml.stop()
        mr.stop()
        print "Programm wurde beendet"

def wait_barrier(distref=0.0, timeout=0.0):
    us = UltrasonicSensor()
    pathclear_t = 0.0

    while True:
        if us.dist_cm > distref and not pathclear_t:
            pathclear_t = time.time()

        if us.dist_cm < distref and pathclear_t:
            pathclear_t = 0.0

        if pathclear_t and (time.time() - pathclear_t) > timeout:
            return

        time.sleep(0.03)

def stop_all_motors():
    for p in [Motor.PORT.A, Motor.PORT.B, Motor.PORT.C, Motor.PORT.D]:
        try:
            Motor(port=p).stop()
        except NoSuchMotorError:
            pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser( sys.argv[0] )
    parser.add_argument( "-Vref", dest="Vref", type=float, default=350 )
    parser.add_argument( "-colmax", dest="colmax", type=float, default=88.0 )           # Reflexionswert auf Hintergrund
    parser.add_argument( "-colmin", dest="colmin", type=float, default=7.0 )            # Reflexionswert auf Linie
    parser.add_argument( "-distref", dest="distref", type=float, default=20.0 )         # Abstand in cm
    parser.add_argument( "-Vtremble", dest="Vtremble", type=float, default=100.0 )      # Zuckelgrenze (Geschwindigkeit)
    parser.add_argument( "-timeout", dest="timeout", type=float, default=0.0 )          # Max. Wartezeit (Zuckeln/PATHCLEAR) in Sekunden
    parser.add_argument( "-cycledelay", dest="cycledelay", type=float, default=0.0 )    # Verlaengerung der Zyklusdauer in Sekunden
    parser.add_argument( "-lKp", dest="lKp", type=float, default=3.5 )
    parser.add_argument( "-lKi", dest="lKi", type=float, default=0.0 )
    parser.add_argument( "-lKd", dest="lKd", type=float, default=2.0 )
    parser.add_argument( "-dKp", dest="dKp", type=float, default=30.0 )
    parser.add_argument( "-dKi", dest="dKi", type=float, default=0.0 )
    parser.add_argument( "-dKd", dest="dKd", type=float, default=0.0 )
    args = parser.parse_args( sys.argv[1:] )

    follow_line(args.Vref, args.colmax, args.colmin, args.distref, args.Vtremble, args.timeout, args.cycledelay, args.lKp, args.lKi, args.lKd, args.dKp, args.dKi, args.dKd)
