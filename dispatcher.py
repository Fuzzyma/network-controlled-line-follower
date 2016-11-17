#!/usr/bin/env python3

import socket
from subprocess import Popen, PIPE
from node.constants import BOT_ADDR, AP_ADDR
import json
from Queue import Queue, Empty
from threading import Thread
import select
import os


class NetworkFunction:
    def __init__(self, executable, priority):
        self.executable = executable
        self.priority = priority
        self.handle = None
        self.queue = Queue()
        self.thread = None

    def start(self):
        if self.started:
            return

        # Open subprocess with network fucntion and connected stdout to output of this nf
        # You can send data to every process by sending something to stdin
        self.handle = Popen('python3 ' + self.executable, stdin=PIPE, stdout=PIPE)

        # To read the stdout of the process we create a new thread
        self.thread = Thread(target=self.read_stdout, args=(self.handle.stdout, self.queue))
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        self.handle.terminate()

    @property
    def started(self):
        return self.handle is not None

    def equals(self, executable):
        return executable == self.executable

    def __eq__(self, other):
        if isinstance(other, NetworkFunction):
            return self.executable == other.executable

    def write_stdin(self, payload, answer=None):
        '''
        Sends a payload to stdin of a nf process.

        :param payload: Data string to be send
        :param answer: Result of the network functions before this one
        :return: None
        '''

        payload = json.loads(payload.decode('utf8'))
        payload["answer"] = answer
        self.handle.stdin.write(json.dumps(payload).encode('utf8'))
        self.handle.stdin.flush()

    @staticmethod
    def read_stdout(out, queue):
        '''
        Read the output of stdout and add it to queue

        :param out: stdout from the nf process
        :param queue: queue the data are added to
        :return: None
        '''
        for line in iter(out.readline, b''):
            queue.put(json.loads(line).decode('utf8'))
        out.close()

    def get_answer(self):
        while True:
            try:
                line = self.queue.get_nowait()  # or q.get(timeout=.1)
            except Empty:
                print('no output yet')
            else:
                return line

    @classmethod
    def readFromFile(cls, filename):
        nfs = []
        with open(filename, encoding='utf8') as f:
            for line in f:
                exe, prio = line.rstrip('\n').split('\t')
                nfs.append(cls(exe, prio))

        return sorted(nfs, key=lambda x: x.priority, reverse=True)


class Dispatcher:
    def __init__(self, filename):
        self.nfs = NetworkFunction.readFromFile(filename)

    def startAll(self):
        for i in nfs:
            i.start()


def nf_file_was_changed(filename):
    last_changed = os.path.getmtime(filename)
    if last_changed > nf_file_was_changed.time:
        nf_file_was_changed.time = last_changed
        return True
    return False

nf_file_was_changed.time = 0


def reread_nf_file(filename):
    nfs = NetworkFunction.readFromFile(filename)

    for i in reread_nf_file.nfs:
        if i not in nfs:
            i.stop()

    for d in nfs:
        d.start()

    reread_nf_file.nfs = nfs
    return nfs

reread_nf_file.nfs = []


def main():
    nfs = []
    cnt = 0
    running = []
    answer = None

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(AP_ADDR)

    filename = "network_functions.txt"

    nfs = reread_nf_file(filename)

    while True:
        readable, writable, exceptional = select.select([sock], [], [sock], 0)

        if not readable:
            if nf_file_was_changed(filename):
                reread_nf_file(filename)
            continue

        try:
            payload, addr = sock.recvfrom(256)
        except (socket.error, socket.herror, socket.gaierror, socket.timeout):
            return False
        else:
            for i in nfs:
                i.write_stdin(payload, answer)
                answer = i.get_answer()

        sock.sendto(json.dumps(answer).encode('utf-8'), BOT_ADDR)
