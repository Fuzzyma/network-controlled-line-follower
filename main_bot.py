#!/usr/bin/env python3

from node.bot import Bot, TimeoutError, BlackLineException
import time


def main():
    b = Bot().reset()
    print("Calibrate")
    b.calibrate()

    input("Press Enter to start")

    i = 0.0
    dropped_packages = 0
    start = time.time()

    benchmark_start = []
    benchmark_control = []
    benchmark_stop = []

    try:
        while True:
            benchmark_start.append(time.time())
            i += 1

            b.send(b.getData(), "DATA")
            try:
                try:
                    speed_left, speed_right = b.receive("CONTROL", timeout=50).getLastCorrection()
                except BlackLineException:
                    b.stop().receive("GO")
                    benchmark_start.pop()
                    continue
            except TimeoutError:
                dropped_packages += 1
                benchmark_start.pop()
                continue
            else:
                benchmark_control.append(time.time())
                b.left(speed_left).right(speed_right)

            benchmark_stop.append(time.time())

    except KeyboardInterrupt:
        b.stop().reset()
        # print("The average loop time was", (time.time() - start)/i * 1000, "ms")
        print(dropped_packages, "Packages where dropped because of AP not responding in time")

        if not len(benchmark_start):
            return

        import operator

        result_global = map(operator.sub, benchmark_stop, benchmark_start)
        result_control = map(operator.sub, benchmark_stop, benchmark_control)
        result_socket = map(operator.sub, benchmark_control, benchmark_start)
        result_global = [i * 1000 for i in result_global]
        result_control = [i * 1000 for i in result_control]
        result_socket = [i * 1000 for i in result_socket]

        print("Mean time:", sum(result_global) / float(len(result_global)))
        print("Max/Min:", max(result_global), '/', min(result_global))

        print("Mean time socket:", sum(result_socket) / float(len(result_socket)))
        print("Max/Min:", max(result_socket), '/', min(result_socket))

        print("Mean time control:", sum(result_control) / float(len(result_control)))
        print("Max/Min:", max(result_control), '/', min(result_control))

        with open('log.txt', 'w+') as f:
            for key, value in enumerate(result_global):
                print("Global", value, file=f)
                print("Socket", result_socket[key], file=f)
                print("Control", result_control[key], file=f)

if __name__ == '__main__':
    # profile.run('main()')
    main()
