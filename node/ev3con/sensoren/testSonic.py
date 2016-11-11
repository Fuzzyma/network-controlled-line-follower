from ev3.lego import UltrasonicSensor
#from util import get_input
import datetime
#get_input('Start')

d = UltrasonicSensor()
distStart = d.dist_cm
timeDiff=datetime.datetime.now()
#Initialisiere System
while distStart == d.dist_cm:
    pass # Sobald sich der Wert aendere beginne mit der Aufzeichnung
timeStart = datetime.datetime.now()
distStart = d.dist_cm
while distStart == d.dist_cm:
    pass# Sobald sich der ert erneut aendert breche die Aufzeichnung ab
timeEnd = datetime.datetime.now()
distEnd = d.dist_cm
timeDiff = timeEnd - timeDiff
print(timeDiff)
distDiff = distEnd - distStart
print(distDiff)
