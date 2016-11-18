#!/usr/bin/env python3

import sys
import time
from queue import Queue, Empty
from threading import Thread
import json
import signal


class TimeoutError(RuntimeError):
    pass


class Piped:
    def __init__(self, source=sys.stdin):
        self.queue = Queue()
        self.thread = Thread(target=self.enqueue_from_source, args=(source, self.queue))
        self.thread.daemon = True
        self.thread.start()
        self.closed = False
        signal.signal(signal.SIGTERM, self.sigterm_handler)

    @staticmethod
    def enqueue_from_source(source, queue):
        for line in iter(source.readline, b''):
            queue.put(line)
        source.close()

    def sigterm_handler(self):
        self.closed = True

    def empty(self):
        return self.queue.empty()

    def push(self, msg):
        print(msg)

    def pushJSON(self, msg):
        self.push(json.dumps(msg))

    def pull(self, timeout=None):
        base = time.time()
        while True:
            try:
                line = self.queue.get_nowait()  # or q.get(timeout=.1)
            except Empty:
                if timeout is not None and base + timeout < time.time():
                    raise TimeoutError
                continue
            else:  # got line
                return line.rstrip()

    def pullJSON(self, timeout=None):
        return json.loads(self.pull(timeout=timeout))

    def pullLast(self, timeout=None):
        base = time.time()
        while True:
            try:
                line = self.pull(timeout=0)
            except TimeoutError:
                if timeout is not None and base + timeout < time.time():
                    raise TimeoutError
                return line
            else:
                continue

    def pullLastJSON(self, timeout=None):
        return json.loads(self.pullLast(timeout=timeout))
