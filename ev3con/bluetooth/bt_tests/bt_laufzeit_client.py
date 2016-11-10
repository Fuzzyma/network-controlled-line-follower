import time

class BTclient:
    def __init__(self):
        self.socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)

    def connect2server(self, sname="btserver", port=1, timeout=5):
        btdev = bluetooth.discover_devices(duration=timeout, lookup_names=True)

        for dev in btdev:
            if dev[1] == sname:
                self.socket.connect((dev[0], port))
                return

    def send(self, data):
        self.socket.send(data)

    def receive(self, size=1024):
        return self.socket.recv(size)

    def close(self):
        self.socket.close()


if __name__ == "__main__":
    btc = BTclient()
    btc.connect2server("thinkpat")

    while True:
        data = btc.receive()
        btc.send(data)
        print "Empfangene Botschaft: " + data
        print type(data)
