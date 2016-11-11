#!/usr/bin/env python3

from node.ap import AP, TimeoutError
import time
import operator

def main():
    ap = AP()

    benchmark_start = []
    benchmark_stop = []

    try:
        print("Requesting Calibration")
        ap.calibrate()

        while True:
            benchmark_start.append(time.time())
            ap.receive("DATA").send(ap.getCorrection(), "CONTROL")
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

        print("Mean time:", sum(result) / float(len(result)))
        print("Max/Min:", max(result), '/', min(result))

        return


if __name__ == '__main__':
    main()
