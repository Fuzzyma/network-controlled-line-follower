# follow_line_topikachu.py - Linienverfolung mit Abstandshaltung
# 12. Juni 2015 - Patrick Ziegler, TU Dresden
#
# Es wird die Bibliothek von topikachu verwendet! Ein Schleifenzyklus
# dauert in der Regel 30 ms, hin und wieder auch bis zu 60 ms.
#
# Beispielhafte Verwendung:
# python follow_line.py -Vref 350 -lKp 2 -lKd 8 -dKp 3
# oder aus Python-Konsole heraus (ohne Parameter) mit:
# execfile('./follow_line.py')

import sys, time, traceback, argparse
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

def follow_line(Vref=0.0, colmax=0.0, colmin=0.0, distref=0.0, lKp=0.0, lKi=0.0, lKd=0.0, dKp=0.0, dKi=0.0, dKd=0.0):
    start_t = 0.0

    pid_line = PID(lKp, lKi, lKd)
    pid_dist = PID(dKp, dKi, dKd)

    ml = Motor(port=Motor.PORT.A)
    mr = Motor(port=Motor.PORT.B)

    cs = ColorSensor()
    us = UltrasonicSensor()

    try:
        ml.run_forever(Vref, speed_regulation=True)
        mr.run_forever(Vref, speed_regulation=True)

        while True:
            start_t = time.time()

            # die Farbwerte werden automatisch auf Bereich [0,100] abgebildet, Differenz zu 50 ist Fehler fuer PID
            pid_line.calc( 50 - ( ( cs.reflect - colmin ) / ( colmax - colmin ) ) * 100 )
            pid_dist.calc( distref - us.dist_cm )

            # es soll nicht auf Hindernis zubeschleunigt werden
            if pid_dist.correction < 0:
                pid_dist.correction = 0

            if pid_line.correction > 0: # im dunklen Bereich
                ml.run_forever( (-1) * ( Vref - pid_dist.correction ) )
                mr.run_forever( (-1) * ( Vref - pid_dist.correction - pid_line.correction ) )
            elif pid_line.correction < 0: # im hellen Bereich
                ml.run_forever( (-1) * ( Vref - pid_dist.correction + pid_line.correction ) )
                mr.run_forever( (-1) * ( Vref - pid_dist.correction ) )

            print "Zyklusdauer: " + str((time.time() - start_t) * 1000) + "ms"

    except:
        ml.stop()
        mr.stop()

        print traceback.format_exc()
        print "Programm wurde beendet"

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

    follow_line(args.Vref, args.colmax, args.colmin, args.distref, args.lKp, args.lKi, args.lKd, args.dKp, args.dKi, args.dKd)
