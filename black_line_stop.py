#!/usr/bin/env python3

from node.piped import Piped
import sys
from node.package import Package


def main():
    p = Piped()
    white = 255
    black = 0

    while not p.closed:
        if p.empty():
            continue

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
                # TODO: send speed instead of correction and do zero speed for 2 seconds
                # print("Black line detected. Stop for 2 secs", file=sys.stderr, flush=True)
                p.pushJSON(Package(type="BLACK_LINE", ack=True).package)
            else:
                p.pushJSON(msg["answer"])

    print("Stopping black_line_stop.py", file=sys.stderr, flush=True)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass