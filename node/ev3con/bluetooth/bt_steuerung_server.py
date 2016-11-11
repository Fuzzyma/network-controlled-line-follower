import time
from connect import *

tgl = True
bth = BTHost()

print "Server gestartet"

while True:
    bth.accept_requests()

    if tgl:
        bth.send2all("on")
        print("Gesendete Botschaft: 'on'")
    else:
        bth.send2all("off")
        print("Gesendete Botschaft: 'off'")

    tgl = not tgl
    time.sleep(0.5)
