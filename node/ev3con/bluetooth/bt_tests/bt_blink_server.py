import time
import bluetooth

port = 1
tgl = True
server = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
server.bind(("", port))
server.listen(1)
server.setblocking(False)
peers = []

while True:
    try:
        bufsock, bufaddr = server.accept()
        peers.append(bufsock)
        print "Neuer Teilnehmer: " + bufaddr[0] + " (" + bluetooth.lookup_name(bufaddr[0], timeout=3) + ")"
    except:
        pass

    start_time = time.time()

    for p in peers:
        try:
            if tgl:
                p.send("on")
            else:
                p.send("off")
        except:
            peers.remove(p)

    end_time = time.time()

    print "Sendezeit: " + str( end_time - start_time ) + " bei " + str(len(peers)) + " Verbindungen"

    tgl = not tgl

    time.sleep(0.5)
