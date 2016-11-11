from ev3.lego import UltrasonicSensor
from util import get_input

get_input('Start')

d = Ultrasonic_Sensor()
distStart = d.dist_cm
#Initialisiere System
while distStart == d.dist_cm:
 pass # Sobald sich der Wert ändere beginne mit der Aufzeichnung
timeStart = datetime.datetime.now()
distStart = d.dist_cm
while distStart == d.dist_cm:
 pass# Sobald sich der ert erneut ändert breche die Aufzeichnung ab
timeEnd = datetime.datetime.now()
distEnd = d.dist_cm
timeDiff = timeEnd - timeDiff
#print(timeDiff)
distDiff = distEnd - distStart
#print(distDiff)
timeDiff
distDiff