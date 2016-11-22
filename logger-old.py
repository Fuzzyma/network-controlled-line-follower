#!/usr/bin/env python3

import sys
import time
from queue import Queue, Empty
from threading import Thread
import signal
import json

def enqueue_input(inp, queue):
    # global log
    for line in iter(inp.readline, b''):
        # log.add("Input to logger:" + queue)
        queue.put(line)
    inp.close()


def sigterm_handler():
    global log
    log.add("Logger was terminated!\n\n")
    del log
    sys.exit()


class Log:
    def __init__(self):
        self.base = time.time()
        self.file = open('logger.txt', 'a')
        self.cache = []

    def add(self, msg):
        self.cache.append("[ {0:.2f} ]: {1}".format((time.time()-self.base), msg.rstrip() + '\n'))
        # self.file.write("[ {0:.2f} ]: {1}".format((time.time()-self.base), msg.rstrip() + '\n'))

    def __del__(self):
        self.file.writelines(self.cache)
        self.file.close()


def main():
    global log
    queue = Queue()
    thread = Thread(target=enqueue_input, args=(sys.stdin, queue))
    thread.daemon = True
    thread.start()

    log.add("Starting Logger")

    signal.signal(signal.SIGTERM, sigterm_handler)

    while True:
        try:
            line = queue.get_nowait()  # or q.get(timeout=.1)
        except Empty:
            continue
        else:  # got line
            print(json.dumps(json.loads(line.rstrip())["answer"]), flush=True)
            log.add(line)

if __name__ == '__main__':
    try:
        log = Log()
        main()
    except KeyboardInterrupt:
        log.add("Stopping Logger")
