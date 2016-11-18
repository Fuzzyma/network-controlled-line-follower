#!/usr/bin/env python3

import socket
from subprocess import Popen, PIPE
from node.constants import BOT_ADDR, AP_ADDR
import json
from queue import Queue, Empty
from threading import Thread
import select
import os
import sys
import time


debug = True


class TimeoutError(RuntimeError):
    pass


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

        print("Starting", self.executable)

        # Open subprocess with network function and connected stdout to output of this nf
        # You can send data to every process by sending something to stdin
        self.handle = Popen([sys.executable, self.executable], stdin=PIPE, stdout=PIPE, stderr=sys.stderr) #open("error.txt", 'a')

        # To read the stdout of the process we create a new thread
        self.thread = Thread(target=self.read_stdout, args=(self.handle.stdout, self.queue, self.executable))
        #self.thread.daemon = True
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

        payload["answer"] = answer

        if debug:
            print("We send to", self.executable + ':', (json.dumps(payload) + '\n').encode('utf8'), "...")
        self.handle.stdin.write((json.dumps(payload) + '\n').encode('utf8'))
        self.handle.stdin.flush()

    @staticmethod
    def read_stdout(out, queue, executable):
        '''
        Read the output of stdout and add it to queue

        :param out: stdout from the nf process
        :param queue: queue the data are added to
        :param executable: name of the process running
        :return: None
        '''
        for line in iter(out.readline, b''):
            if debug:
                print("We read from", executable + ':', line, "...")
                print("We made it to", line.decode('utf8').rstrip(), '...')
            queue.put(json.loads(line.decode('utf8').rstrip()))
        out.close()

    def get_answer(self, timeout=None):
        base = time.time()
        while True:
            try:
                line = self.queue.get_nowait()  # or q.get(timeout=.1)
            except Empty:
                if timeout is not None and base + timeout/1000.0 < time.time():
                    raise TimeoutError
                continue
            else:
                return line

    def has_answer(self):
        return not self.queue.empty()

    @classmethod
    def readFromFile(cls, filename):
        nfs = []
        with open(filename, encoding='utf8') as f:
            for line in f:
                exe, prio = line.rstrip('\n').split('\t')
                nfs.append(cls(exe, prio))

        return sorted(nfs, key=lambda x: x.priority, reverse=True)


class Socket:
    def __init__(self):
        # setup socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(AP_ADDR)

        # Use blocking methods
        self.sock.setblocking(True)

        self.received = {
            "id": 0,
            "data": None,
            "ack": False,
            "time": 0,
            "type": None,
            "referer": None
        }  # data last received

    def send(self, data):
        self.sock.sendto(json.dumps(data).encode('utf-8'), BOT_ADDR)
        return self

    def sendAck(self):
        self.send({
            'id':0,
            'type': 'ACK',
            'ack': False
        })
        return self

    def sendEnsured(self, data, timeout=None, interval=1000):
        start = time.time()

        while True:
            try:
                self.send(data).receive('ACK', interval)
                break
            except TimeoutError:
                if timeout is not None and time.time() - start > timeout / 1000.0:
                    raise TimeoutError
                continue
        return self

    def sendWithEnsureCheck(self, data, timeout=None):
        if data["ack"]:
            self.sendEnsured(data, timeout=timeout)
        else:
            self.send(data)

    def is_readable(self):
        readable, writable, exceptional = select.select([self.sock], [], [self.sock], 0)
        return bool(readable)

    def tryReceive(self, type=None):
        if not self.is_readable():
            return False

        try:
            payload, addr = self.sock.recvfrom(256)
        except (socket.error, socket.herror, socket.gaierror, socket.timeout):
            return False
        else:
            self.received = json.loads(payload.decode("utf-8"))

        if self.received["ack"]:
            self.sendAck()

        if type is None or type == self.received['type']:
            return True

        return False

    def receive(self, type=None, timeout=None):
        start = time.time()

        while not self.tryReceive(type):
            if timeout is not None and time.time() - start > timeout / 1000.0:
                raise TimeoutError
            continue

        return self


def nf_file_was_changed(filename):
    last_changed = os.path.getmtime(filename)
    if last_changed > nf_file_was_changed.time:
        nf_file_was_changed.time = last_changed
        return True
    return False

nf_file_was_changed.time = 0


def reread_nf_file(filename):

    res = []

    for d in NetworkFunction.readFromFile(filename):
        if d not in reread_nf_file.nfs:
            d.start()
            res.append(d)
        else:
            res.append(reread_nf_file.nfs[reread_nf_file.nfs.index(d)])

    for d in reread_nf_file.nfs:
        if d not in res:
            d.stop()

    reread_nf_file.nfs = res

    return res

reread_nf_file.nfs = []


def main():
    sock = Socket()

    main.sock = sock

    filename = "network_functions.txt"

    print("Reading", filename)
    nf_file_was_changed(filename)
    nfs = reread_nf_file(filename)
    print("Got", len(nfs), "network functions")
    print(list(map(lambda x: x.executable, nfs)))

    # Initialisation
    # Check if any process want to say something
    for i in nfs:
        print("Getting answer from", i.executable)
        try:
            answer = i.get_answer(timeout=1000)
        except TimeoutError:
            print(i.executable, "has nothing to say")
            continue
        else:
            print("Sending:", answer)
            sock.sendWithEnsureCheck(answer)

    print("Starting main loop")

    while True:
        if not sock.is_readable():
            if nf_file_was_changed(filename):
                print(filename, "was changed. Updating...")
                nfs = reread_nf_file(filename)
                print("Got", len(nfs), "network functions")
                print(list(map(lambda x: x.executable, nfs)))
            continue

        answer = None

        if not sock.receive():
            continue

        data = sock.received
        if debug:
            print("Received data: ", data)

        for i in nfs:
            i.write_stdin(data, answer)
            answer = i.get_answer()

        if debug:
            print("Sending data", answer)

        sock.sendWithEnsureCheck(answer)

main.sock = None

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        for i in reread_nf_file.nfs:
            i.stop()
            try:
                answer = i.get_answer(timeout=1000)
                print(answer)
            except TimeoutError:
                continue
            else:
                try:
                    main.sock.sendWithEnsureCheck(answer, timeout=2000)
                except TimeoutError:
                    continue
        sys.exit()
