#!/usr/bin/env python3

from node.ap import AP as BaseAP
import time
import operator
import sys
import json
from queue import Queue, Empty
from threading import Thread
from node.constants import DEBUG, ShutdownException
from node.piped import SIG


class AP(BaseAP):
    def __init__(self):
        super(AP, self).__init__(sockets=False)
        self.queue = Queue()
        self.thread = Thread(target=self.enqueue_input, args=(sys.stdin, self.queue))
        self.thread.daemon = True
        self.thread.start()

    def send_implementation(self, payload):
        if DEBUG >= 2:
            print("[main_ap.py] Sending:", payload, flush=True, file=sys.stderr)
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
            if DEBUG >= 2:
                print("[main_ap.py] received", line, flush=True, file=sys.stderr)
            self.received = json.loads(line)
            return True

    # Overwrite sendEnsured since that functionality is provided by the dispatcher
    def sendEnsured(self, data=None, type='CONTROL', timeout=None, interval=1000, last=False):
        return self.send(data, type, ack=True, last=last)


def main():

    sig = SIG()

    if len(sys.argv) > 1 and sys.argv[1] == 'socket':
        ap = BaseAP()
        print("[ main_ap.py ] Requesting Calibration", file=sys.stderr)
        ap.calibrate()
    else:
        ap = AP()

    benchmark_start = []
    benchmark_stop = []

    try:
        while not sig.closed:

            benchmark_start.append(time.time())
            try:
                ap.receive("DATA", timeout=100).send(ap.getCorrection(), "CONTROL")
            except TimeoutError:
                benchmark_start.pop()
                continue
            benchmark_stop.append(time.time())
    except ShutdownException:
        pass

    print("[ main_ap.py ] Shutdown", file=sys.stderr)
    try:
        ap.sendEnsured(type="CONTROL", data=[0, 0], timeout=2000, last=True)
    except TimeoutError:
        pass

    if not len(benchmark_start):
        return

    result = map(operator.sub, benchmark_stop, benchmark_start)
    result = [i * 1000 for i in result]

    if len(result):
        print("[ main_ap.py ] Mean time:", sum(result) / float(len(result)), file=sys.stderr)
        print("[ main_ap.py ] Max/Min:", max(result), '/', min(result), file=sys.stderr)

    sys.exit()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
