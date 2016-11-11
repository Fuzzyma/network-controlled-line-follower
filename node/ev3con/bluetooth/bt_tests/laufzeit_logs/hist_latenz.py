#/usr/bin/python

import numpy as np
import matplotlib.pyplot as plt

bt_latenz = np.loadtxt("laufzeit_bt_flur")
wlan_latenz = np.loadtxt("laufzeit_wlan_zuhause")

bty, btx = np.histogram(bt_latenz, bins=500)
wlany, wlanx = np.histogram(wlan_latenz, bins=1000)

btx = btx[1:] * 1000
wlanx = wlanx[1:]

bty = bty.astype("float64") / np.amax(bty)
wlany = wlany.astype("float64") / np.amax(wlany)

plt.figure(figsize=(10,4.5))
plt.semilogx(btx, bty, "dodgerblue", wlanx, wlany, "k")
plt.xlim(1, 100)
plt.ylim(0, 1.1)
plt.grid()

xpos = [ 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 20, 30, 40, 50, 60, 70, 80, 90 ]
xlbl = ( "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "20", "30", "40", "50", "60", "70", "80", "90" )
plt.xticks(xpos, xlbl)
plt.legend(("Bluetooth","WLAN"))

plt.title("Normiertes Histogramm der Latenzzeiten")
plt.xlabel("Latenzzeit in ms")
plt.ylabel("h(x) / max(h(x))")

plt.savefig("./hist_latenz.pdf")
plt.show()
