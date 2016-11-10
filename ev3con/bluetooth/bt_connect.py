import bluetooth

class BTClient:
    def __init__(self):
        self.csock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        self.sname = "NOCH NICHT VERBUNDEN"

    def connect(self, sname="88:9F:FA:F0:C0:88", discover_timeout=4, connect_timeout=None, port=1):
        self.sname = sname
        self.csock.settimeout(connect_timeout)

        btdev = bluetooth.discover_devices(duration=discover_timeout, lookup_names=True)
        for dev in btdev:
            if dev[0] == sname or dev[1] == sname:
                print "Server " + str(sname) + " gefunden, versuche Verbindungsaufbau"
                try:
                    self.csock.connect((dev[0], port))
                except:
                    print "Verbindungsaufbau mit " + str(sname) + " an Port " + str(port) + " gescheitert!"
                    self.csock.settimeout(None)
                    return
                print "Verbindung mit " + str(sname) + " an Port " + str(port) + " hergestellt"
                self.csock.settimeout(None)
                return

        print "Server " + str(sname) + " nicht gefunden!"
        self.csock.settimeout(None)

    def send(self, data, send_timeout=None):
        self.csock.settimeout(send_timeout)

        try:
            self.csock.send(data)
            print "Botschaft: '" + str(data) + "' gesendet an " + str(self.sname)
        except:
            print "Senden an " + str(self.sname) + " gescheitert"

        self.csock.settimeout(None)

    def receive(self, size=1024, recv_timeout=None):
        self.csock.settimeout(recv_timeout)

        try:
            data = self.csock.recv(size)
            print "Botschaft: '" + str(data) + "' empfangen von " + str(self.sname)
            self.csock.settimeout(None)
            return data
        except:
            print "Empfangen von " + str(self.sname) + " gescheitert"
            self.csock.settimeout(None)
            return None

    def close(self):
        self.csock.close()

class BTHost:
    def __init__(self, port=1):
        self.port = port
        self.peersocks = []
        self.hostsock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        self.hostsock.bind(("", port))
        self.hostsock.listen(1)

    def accept_requests(self, lookup_timeout=2):
        self.hostsock.setblocking(False)

        while True:
            try:
                bufsock, bufaddr = self.hostsock.accept()
            except:
                self.hostsock.setblocking(True)
                return

            try:
                self.peersocks.append((bufsock, bufaddr[0], bluetooth.lookup_name(bufaddr[0], lookup_timeout)))
            except:
                self.peersocks.append((bufsock, bufaddr[0], "kein Name gefunden"))

            print "Neuer Teilnehmer: " + self.peersocks[len(self.peersocks)-1][1] + " (" + self.peersocks[len(self.peersocks)-1][2] + ")"

    def send(self, paddr, data, send_timeout=None):
        self.hostsock.settimeout(send_timeout)

        for p in self.peersocks:
            if p[1] == paddr or p[2] == paddr:
                try:
                    p[0].send(data)
                    print "Botschaft: '" + str(data) + "' gesendet an " + str(paddr)
                except:
                    self.peersocks.remove(p)
                    print "Verbindung zu " + p[1] + " (" + p[2] + ") verloren!"

        self.hostsock.settimeout(None)

    def send2all(self, data, send_timeout=None):
        self.hostsock.settimeout(send_timeout)

        for p in self.peersocks:
            try:
                p[0].send(data)
            except:
                self.peersocks.remove(p)
                print "Verbindung zu " + p[1] + " (" + p[2] + ") verloren!"

        print "Botschaft: '" + str(data) + "' gesendet an " + str(len(self.peersocks)) + " Peers"
        self.hostsock.settimeout(None)

    def receive(self, paddr, size=1024, recv_timeout=None):
        data = ""
        self.hostsock.settimeout(recv_timeout)

        for p in self.peersocks:
            if p[1] == paddr or p[2] == paddr:
                try:
                    data = p[0].recv(size)
                    print "Botschaft: '" + str(data) + "' empfangen von " + str(paddr)
                except:
                    self.peersocks.remove(p)
                    print "Verbindung zu " + p[1] + " (" + p[2] + ") verloren!"

        self.hostsock.settimeout(None)
        return data

    def close(self):
        self.hostsock.close()
        for p in self.peersocks:
            p[0].close()
