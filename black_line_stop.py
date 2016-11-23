#!/usr/bin/env python3

from node.piped import Piped, SIG
import sys
from node.package import Package
import time
from node.constants import DEBUG


def main():
    p = Piped(name="black_line_stop.py")
    white = 255
    black = 0
    base = 0

    sig = SIG()
    flag = False

    while not sig.closed:
        if p.empty():
            continue

        while not p.empty():
            msg = p.pullJSON()
            if msg["type"] == "CALIBRATION_DATA":
                white, black = msg["data"]
                continue

            if msg["type"] == "SHUTDOWN":
                sig.closed = True
                break

            # Dont handle this package. Pipe it to next process
            if msg["type"] != 'DATA' or (msg["answer"] is not None and msg["answer"]["last"]):
                p.repush(msg)
                continue

            left, right = msg["data"]

            grey_l = ((left - black) / (white - black)) * 255
            grey_r = ((right - black) / (white - black)) * 255

            grey = (grey_l + grey_r) / 2

            # print(grey, flush=True, file=sys.stderr)

            if grey < 100 or flag:
                if not flag:
                    base = time.time()
                    flag = True
                    if DEBUG:
                        print("[ black_line_stop.py ] Black line detected. Stop for 2 secs", file=sys.stderr, flush=True)

                p.pushJSON(Package(type="CONTROL", data=[0, 0]).package)

                if base + 2 < time.time():
                    flag = False
                    if DEBUG:
                        print("[ black_line_stop.py ] 2 seconds over - resuming", file=sys.stderr, flush=True)

                continue

            p.pushJSON(msg["answer"] if msg["answer"] is not None else None)

    print("[ black_line_stop.py ] Shutdown ", file=sys.stderr, flush=True)

if __name__ == "__main__":
    main()
