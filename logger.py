#!/usr/bin/env python3

from node.piped import Piped
import json
import time


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
    p = Piped()
    l = Log()

    while not p.closed:
        if p.empty():
            continue

        while not p.empty():
            msg = p.pullJSON()
            p.repush(msg)
            l.add(json.dumps(msg))

    l.add("Stopping Logger")
    l.close()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass

