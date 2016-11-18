#!/usr/bin/env python3

from node.ap import AP as BaseAP, TimeoutError
import time
import operator
import sys
import json
from queue import Queue, Empty
from threading import Thread
import signal

class AP(BaseAP):
    def __init__(self):
        super(AP, self).__init__(sockets=False)
        self.queue = Queue()
        self.thread = Thread(target=self.enqueue_input, args=(sys.stdin, self.queue))
        self.thread.daemon = True
        self.thread.start()

    def send_implementation(self, payload):
        print(payload, flush=True)
        return self

    @staticmethod
    def enqueue_input(inp, queue):
        for line in iter(inp.readline, b''):
            queue.put(line)
        inp.close()

    def receive_implementation(self):
        try:
            line = self.queue.get_nowait()  # or q.get(timeout=.1)
        except Empty:
            return False
        else:  # got line
            self.received = json.loads(line)
            return True

    # Overwrite sendEnsured since that functionality is provided by the dispatcher
    def sendEnsured(self, data=None, type='CONTROL', timeout=None, interval=1000):
        return self.send(data, type, ack=True)


shutdown = False

def sigterm_handler():
    shutdown = True

def main():
    ap = AP()

    benchmark_start = []
    benchmark_stop = []

    signal.signal(signal.SIGTERM, sigterm_handler)

    try:
        print("Requesting Calibration", file=sys.stderr)
        ap.calibrate()

        while True:
            if shutdown:
                raise KeyboardInterrupt
            benchmark_start.append(time.time())
            try:
                ap.receive("DATA", timeout=100).send(ap.getCorrection(), "CONTROL")
            except TimeoutError:
                benchmark_start.pop()
                continue
            benchmark_stop.append(time.time())
    except KeyboardInterrupt:
        try:
            ap.sendEnsured(type="STOP", timeout=2000)
        except TimeoutError:
            pass

        if not len(benchmark_start):
            return

        result = map(operator.sub, benchmark_stop, benchmark_start)
        result = [i * 1000 for i in result]

        print("Mean time:", sum(result) / float(len(result)), file=sys.stderr)
        print("Max/Min:", max(result), '/', min(result), file=sys.stderr)

        sys.exit()


if __name__ == '__main__':
    main()