import time


class RunningAverage(object):
    """Klasse zur Berechnung des laufenden Mittelwertes von avg_size vielen  Werten"""

    def __init__(self, avg_size, start_val=0):
        if avg_size < 1:
            avg_size = 1
        self.avg = int(avg_size) * [start_val]
        self._count = 0

    def calc(self, val):
        self.avg[self._count] = val
        self._count += 1
        if self._count >= len(self.avg):
            self._count = 0
        return sum(self.avg) / len(self.avg)


class PID(object):
    """PID-Controller mit wahlweise Antiwindup und Mittelung von beliebig vielen Differentialwerten"""

    def __init__(self, kp=0, ki=0, kd=0, **kwargs):
        """
        Init-Argumente:
        kp: Proportionalkonstante (default=0)
        ki: Integralkonstante (default=0)
        kd: Differentialkonstante (default=0)

        zusaetzlich moegliche Keyword Argumente:
        antiwindup: Begrenzen des Integralanteils (default=0)
        avgsize_d: Anzahl der zumittelnden Differentialwerte (default=1)
        maxval: Maximalwert
        """
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.antiwindup = 0  # Begrenzen des Integralteils(wenn antiwindup>0)
        self._int_sum = 0  # Integralsumme
        self._old = 0  # vorheriger Fehler
        self._clock_old = 0
        self.avgsize_d = 1
        self.maxval = 0
        self._d_avg = None
        for k in kwargs:
            v = kwargs[k]
            if v is not None:
                setattr(self, k, v)

    def calc(self, ist, soll):
        """
        Berechnet den Stellwert

        Keyword Argumente:
        ist: Momentanwert
        soll:Sollwert

        returns: float
        """
        clock = time.clock()
        dt = (clock - self._clock_old) * 100  # da ansonsten sehr klein
        error = soll - ist

        # Integral
        i = self._int_sum + error * dt
        if self.antiwindup != 0:
            if i > self.antiwindup:
                i = self.antiwindup
            elif i < -self.antiwindup:
                i = -self.antiwindup
        self._int_sum = i

        # Differential
        try:
            d = (error - self._old) / dt
        except ZeroDivisionError:
            d = 0
            print("Zero Division!")

        if self._d_avg:
            d = self._d_avg.calc(d)

        out = self.kp * error + self.ki * i + self.kd * d
        self._clock_old = clock
        self._old = error

        if self.maxval:
            if out > self.maxval:
                out = self.maxval
            elif out < -self.maxval:
                out = -self.maxval
        return out

    @property
    def avgsize_d(self):
        return self.avgsize_d

    @avgsize_d.setter
    def avgsize_d(self, size):
        if size <= 1:
            self._d_avg = None

        size = int(size)
        self._d_avg = RunningAverage(size)
