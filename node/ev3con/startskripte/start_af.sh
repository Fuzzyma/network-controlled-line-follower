#!/bin/bash

# Optionale Parameter:
# ------------------------------------------------------------------------------------
# Option            Std.-Wert           Beschreibung
# -Vref             350                 Grundgeschwindigkeit
# -colmax           88                  Reflexionswert auf Hintergrund
# -colmin           7                   Reflexionswert auf Linie
# -distref          20                  Sollabstand in cm
# -Vtremble         100                 Zuckelgrenze (Geschwindigkeit)
# -timeout          0                   Max. Wartezeit (Zuckeln/PATHCLEAR) in Sekunden
# -cycledelay       0                   Verlaengerung der Zyklusdauer in Sekunden
# -lKp              3.5                 P-Anteil der Farbwertsregelung
# -lKi              0                   I-Anteil der Farbwertsregelung
# -lKd              2                   D-Anteil der Farbwertsregelung
# -dKp              30                  P-Anteil der Abstandsregelung
# -dKi              0                   I-Anteil der Abstandsregelung
# -dKd              0                   D-Anteil der Abstandsregelung
# ------------------------------------------------------------------------------------

# Beispielhafte Verwendung:
# python /home/ev3con/python-ev3con/autonomes_fahren.py -colmax 33

python /home/ev3con/python-ev3con/autonomes_fahren.py

sleep 2
