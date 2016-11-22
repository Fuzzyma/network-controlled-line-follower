from ev3dev.ev3 import LargeMotor


class NotConnectedError(Exception):
    pass


class MotorControl(object):
    """Klasse zum Verbinden und Ansteueren mehrere Motoren gleichzeitg

    Attribute:
    margin: Maximalwert Geschwindigkeit (mit Speedregulation)
    motors: Dictionary mit den jeweiligen Motoren(value) und Ports(key)
    """

    def __init__(self, ports='ABCD', **kwargs):
        """INIT-Argument:
            ports = Ports der Motoren
        """

        self.margin = 1000
        self.motors = {}
        self.ports = ports
        self.attach_motors()

    def set_speed(self, speed, ports='ABCD'):
        """setzt eine Geschwindigkeit(additiv zur mittleren) und schreibt den Wert an bestimmte/alle Motoren

        Keyword Argumente:
        sp = zu setzende Geschwindigkeit
        ports= Portliste/string der anzusteuernden Motoren
        """

        for p in ports:
            if self.motors[p].connected:
                self.motors[p].run_forever(speed_sp=speed, speed_regulation=True)
            else:
                raise NotConnectedError(p)

    def attach_motors(self):
        """Motoren an allen  Ports finden"""
        self.motors = {}
        for p in self.ports:
            self.motors[p] = LargeMotor('out' + p)
            if not self.motors[p].connected:
                raise NotConnectedError(p)

    def stop(self):
        """Stopt alle Motoren

        Keyword Argument:
        ports= Portliste/string der anzusteuernden Motoren
        """

        for p in self.ports:
            if self.motors[p].connected:
                self.motors[p].stop()

    def reset(self):
        """Resetet alle Motoren

        Keyword Argument:
        ports= Portliste/string der anzusteuernden Motoren
        """

        for p in self.ports:
            if self.motors[p].connected:
                self.motors[p].reset()
