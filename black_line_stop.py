#!/usr/bin/env python3

from node.piped import Piped
import sys
from node.package import Package


class BlackLineException(RuntimeError):
    pass


def main():
    p = Piped()
    white = 255
    black = 0

    while not p.closed:
        if p.empty():
            continue

        print("Some Package arrived", file=sys.stderr, flush=True)

        while not p.empty():
            msg = p.pullJSON()
            if msg["type"] == "CALIBRATION_DATA":
                white, black = msg["data"]

            # Dont handle this package. Pipe it to next process
            if msg["type"] != 'DATA':
                p.pushJSON(msg["answer"])
                continue

            left, right = msg["data"]

            grey_l = ((left - black) / (white - black)) * 255
            grey_r = ((right - black) / (white - black)) * 255

            grey = (grey_l + grey_r) / 2

            if grey < 20:
                print("Black line detected. Stop motors immediately", file=sys.stderr, flush=True)
                p.pushJSON(Package(type="STOP", ack=True).package)
            else:
                p.pushJSON(msg["answer"])

    print("Stopping black_line_stop.py", file=sys.stderr, flush=True)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass