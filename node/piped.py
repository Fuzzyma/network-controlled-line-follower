#!/usr/bin/env python3

import sys
import time
from queue import Queue, Empty
from threading import Thread, Event
import json
import signal
from node.constants import DEBUG


class Piped:
    def __init__(self, source=sys.stdin, dest=sys.stdout, name="Unknown"):
        self.queue = Queue()
        self.event = Event()
        self.thread = Thread(target=self.enqueue_from_source, args=(source, self.queue, self.event))
        self.thread.daemon = True
        self.thread.start()
        self.closed = False
        self.dest = dest
        self.exe = name

    @staticmethod
    def enqueue_from_source(source, queue, event):
        for line in iter(source.readline, b''):
            if event.isSet():
                break
            if DEBUG:
                pass  # print("We read:", line, "ENDL", file=sys.stderr, flush=True)
            if line.rstrip() == "":
                # print("[", self.exe, "] Empty Message", file=sys.stderr, flush=True)
                continue
            queue.put(json.loads(line))
        source.close()

    def empty(self):
        return self.queue.empty()

    def push(self, msg):
        if DEBUG:
            print("[", self.exe, "] We push: ", msg, file=sys.stderr, flush=True)
        print(msg, flush=True, file=self.dest, end="\n")

    def pushJSON(self, msg):
        self.push(json.dumps(msg))

    def repush(self, data):
        if data["answer"] is None:
            self.pushJSON(data)
        else:
            self.pushJSON(data["answer"])

    def pull(self, timeout=None):
        base = time.time()
        while True:
            try:
                line = self.queue.get_nowait()  # or q.get(timeout=.1)
            except Empty:
                if timeout is not None and base + timeout/1000.0 < time.time():
                    raise TimeoutError
                continue
            else:  # got line
                if DEBUG:
                    print("[", self.exe, "] We pull from queue: ", line, flush=True, file=sys.stderr)
                return line

    def pullJSON(self, timeout=None):
        return self.pull(timeout=timeout)

    def pullLast(self, timeout=None):
        base = time.time()
        line = None
        while True:
            try:
                line = self.pull(timeout=0)
            except TimeoutError:
                if line is not None:
                    return line
                if timeout is not None and base + timeout/1000.0 < time.time():
                    raise TimeoutError
                continue
            else:
                continue

    def pullLastJSON(self, timeout=None):
        return self.pullLast(timeout=timeout)

    def terminate(self):
        self.event.set()

class SIG:
    def __init__(self):
        signal.signal(signal.SIGTERM, self.sigterm_handler)
        signal.signal(signal.SIGINT, self.sigterm_handler)
        self.closed = False

    def sigterm_handler(self, a, b):
        self.closed = True
