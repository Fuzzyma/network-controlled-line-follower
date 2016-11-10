#!/usr/bin/env python3

from node.bot import Bot, TimeoutError
import time


def main():
    b = Bot().reset()
    print("Calibrate")
    b.calibrate()

    i = 0.0
    dropped_packages = 0
    start = time.time()

    try:
        while True:
            i += 1

            b.send(b.getData(), "DATA")
            try:
                dv = b.receive("CONTROL", timeout=50).getLastCorrection()
            except TimeoutError:
                dropped_packages += 1
                continue
            else:
                b.left(dv).right(dv)

    except KeyboardInterrupt:
        b.stop().reset()
        print("The average loop time was", (time.time() - start)/i * 1000, "ms")
        print(dropped_packages, "Packages where dropped because of AP not responding in time")

if __name__ == '__main__':
    # profile.run('main()')
    main()
