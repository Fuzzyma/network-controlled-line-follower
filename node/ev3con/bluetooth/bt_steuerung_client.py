from ev3.ev3dev import LED
from connect import *

# Host ist:
# thinkpat - 88:9F:FA:F0:C0:88 (Patrick)
# ubuntu-0 - 80:19:34:F4:DD:F9 (Justus)

btc = BTClient()
btc.connect("thinkpat")

led = LED()
led.left.color=LED.COLOR.RED
led.left.off()

print "Beginne Empfang"

while True:
    data = btc.receive()

    if data == "on":
        led.left.on()
    elif data == "off":
        led.left.off()
    elif data == None:
        print "Verbindung zu Server verloren!"
        exit()
