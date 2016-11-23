#!/usr/bin/env python3

from node.piped import Piped, SIG
import json
import time
import sys

class Log:
    def __init__(self):
        self.base = time.time()
        self.file = open('logger.txt', 'a')
        self.cache = []

    def add(self, msg):
        self.cache.append("[ {0:.2f} ]: {1}".format((time.time()-self.base), msg + '\n'))
        # self.file.write("[ {0:.2f} ]: {1}".format((time.time()-self.base), msg.rstrip() + '\n'))

    def close(self):
        self.file.writelines(self.cache)
        self.file.close()


def main():
    p = Piped(name="logger.py")
    l = Log()
    sig = SIG()

    while not sig.closed:
        if p.empty():
            continue

        while not p.empty():
            msg = p.pullJSON()
            if msg["type"] == "CALIBRATION_DATA":
                continue
            p.repush(msg)
            l.add(json.dumps(msg))
            if msg["type"] == "SHUTDOWN":
                sig.closed = True
                break

    l.add("Stopping Logger")
    l.close()
    print("Stopping Logger", flush=True, file=sys.stderr)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass

