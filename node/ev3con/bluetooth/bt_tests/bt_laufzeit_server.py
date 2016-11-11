import time

class BTserver:
    def __init__(self, port=1):
        self.server = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        self.server.bind(("", port))
        self.server.listen(8)
        self.peer, self.paddr = self.server.accept()

    def send(self, data):
        self.peer.send(data)

    def receive(self, size=1024):
        return self.peer.recv(size)

    def close(self):
        self.peer.close()
        self.server.close()


if __name__ == "__main__":
    bts = BTserver()
    i = 0.0
    print "Server wurde gestartet"

    while True:
        start_time = time.time()

        bts.send("Botschaft %f" % i )
        bts.receive()

        end_time = time.time()

        print "%f" % ( end_time - start_time )
        i = i + 1

        #time.sleep(1)
