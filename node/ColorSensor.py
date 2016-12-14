from ev3dev.ev3 import ColorSensor as BaseColorSensor


class ColorSensor(BaseColorSensor):
    """Erweitert die Attribute des Farbsensors"""
    def __init__(self, port=None):
        BaseColorSensor.__init__(self, address=(port if port is None else str(port)))
        self.mode = BaseColorSensor.MODE_RGB_RAW

    @property
    def grey(self):
        """gibt den Grauwert aus"""
        return sum((self.value(0), self.value(1), self.value(2)))/3
