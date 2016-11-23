#!/usr/bin/env python3

import socket
from subprocess import Popen, PIPE
from node.constants import BOT_ADDR, AP_ADDR, DEBUG
import json
import select
import os
import sys
import time
import operator
from node.piped import Piped
from node.package import Package


class NoneException(Exception):
    pass


class NetworkFunction:
    def __init__(self, executable, priority):
        self.executable = executable
        self.priority = priority
        self.handle = None
        self.pipe = None
        self.pending_stop = False
        self.final_package = None

    def start(self, calibration):
        if self.started:
            return

        print("[!dispatcher.py ] Starting", self.executable)

        # Open subprocess with network function and connected stdout to output of this nf
        # You can send data to every process by sending something to stdin
        self.handle = Popen([sys.executable, self.executable], stdin=PIPE, stdout=PIPE, stderr=sys.stderr, bufsize=4000, universal_newlines=True) #open("error.txt", 'a')

        self.pipe = Piped(source=self.handle.stdout, dest=self.handle.stdin, name="dispatcher.py -> "+self.executable)

        self.write_stdin(calibration)

    def stop(self):
        if self.pending_stop:
            return

        # Wait for shield to be stopped from signal
        print("[!dispatcher.py ] Stopping", self.executable)
        self.pipe.pushJSON(Package(type="SHUTDOWN").package)
        self.pending_stop = True
        self.handle.wait()
        print("[!dispatcher.py ] Stopped", self.executable)

    @property
    def started(self):
        return self.handle is not None

    def equals(self, executable):
        return executable == self.executable

    def __eq__(self, other):
        if isinstance(other, NetworkFunction):
            return self.executable == other.executable

    def write_stdin(self, payload, answer=None):
        """
        Sends a payload to stdin of a nf process.

        :param payload: Data string to be send
        :param answer: Result of the network functions before this one
        :return: None
        """

        if self.pending_stop:
            return

        payload["answer"] = answer

        if DEBUG:
            print("[!dispatcher.py ] We send to", self.executable + ':', json.dumps(payload))

        self.pipe.pushJSON(payload)

    def get_answer(self, timeout=None):
        if self.final_package is not None:
            return self.final_package

        answer = self.pipe.pullJSON(timeout=timeout)
        if answer is None:
            raise NoneException
        if answer["last"]:
            self.final_package = answer

        return answer

    def get_last_answer(self, timeout=None):
        if self.final_package is not None:
            return self.final_package

        base = time.time()

        while True:
            if timeout is not None and base + timeout/1000.0 < time.time():
                raise TimeoutError
            answer = self.pipe.pullJSON(timeout=timeout)
            if answer is None:
                raise NoneException
            if answer["last"]:
                self.final_package = answer
                return answer

    def has_answer(self):
        return not self.pipe.empty()

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
        if DEBUG >= 2:
            print("[!dispatcher.py ] Sending data", data)
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

        if DEBUG >= 2:
            print("[!dispatcher.py ] Received data: ", self.received)

        return self

    def calibrate(self):
        calibration_data = self.sendEnsured(Package(type='CALIBRATION_REQUEST', ack=True).package).receive('CALIBRATION_DATA').received
        calibration_data["ack"] = False
        # self.midpoint = (white - black) / 2 + black

        if DEBUG:
            print("[!dispatcher.py ] Got calibration data:", calibration_data)
        return calibration_data


def nf_file_was_changed(filename):
    last_changed = os.path.getmtime(filename)
    if last_changed > nf_file_was_changed.time:
        nf_file_was_changed.time = last_changed
        return True
    return False

nf_file_was_changed.time = 0


def reread_nf_file(filename, calibration):

    res = []

    for d in NetworkFunction.readFromFile(filename):
        if d not in reread_nf_file.nfs:
            d.start(calibration)
            res.append(d)
        else:
            res.append(reread_nf_file.nfs[reread_nf_file.nfs.index(d)])

    for d in reread_nf_file.nfs:
        if d not in res:
            d.stop()

    reread_nf_file.nfs = res

    return res

reread_nf_file.nfs = []

benchmark1 = []
benchmark2 = []


def main():
    # sig = SIG()

    nfs = []
    sock = Socket()

    try:

        calibration = sock.calibrate()

        filename = "network_functions.txt"

        nf_file_was_changed(filename)
        nfs = reread_nf_file(filename, calibration)
        new = nfs
        print("[!dispatcher.py ] Got", len(nfs), "network functions:", list(map(lambda x: x.executable, nfs)))

        print("[!dispatcher.py ] Starting main loop")

        while True:
            if not sock.is_readable():
                if nf_file_was_changed(filename):
                    print("[!dispatcher.py ]", filename, "was changed. Updating...")
                    new = reread_nf_file(filename, calibration)
                    print("[!dispatcher.py ] Got", len(new), "network functions", list(map(lambda x: x.executable, new)))
                continue

            answer = None

            # Continue if nothing was received
            if not sock.receive():
                continue

            # Continue if no network function was found
            if not len(nfs):
                nfs = new
                continue

            data = sock.received

            benchmark1.append(time.time())

            print(list(map(lambda x: x.executable, nfs)))

            try:
                for i in nfs:
                    i.write_stdin(data, answer)
                    answer = i.get_answer(timeout=50)
            except (NoneException, TimeoutError) as i:
                if DEBUG:
                    print("[!dispatcher.py ] No answer from nfs or timeout", i)
                nfs = new
                continue

            benchmark2.append(time.time())

            sock.sendWithEnsureCheck(Package.clean(answer))

            nfs = new
    except KeyboardInterrupt:
        print("[!dispatcher.py ] Stop dispatcher")

        for i in nfs:
            i.stop()
            try:
                print("[!dispatcher.py ] Getting last answer from", i.executable)
                answer = i.get_last_answer(timeout=1000)
            except (NoneException, TimeoutError) as i:
                print("[!dispatcher.py ] No answer from nfs or timeout", i)
                continue
            else:
                try:
                    print("[!dispatcher.py ] Sending last message:", answer)
                    sock.sendWithEnsureCheck(answer, timeout=2000)
                except TimeoutError:
                    continue

        try:
            sock.sendEnsured(Package(type="STOP", ack=True).package, timeout=2000)
        except TimeoutError:
            pass

        result = map(operator.sub, benchmark2, benchmark1)
        result = [i * 1000 for i in result]

        if len(result):
            print("Mean time:", sum(result) / float(len(result)))
            print("Max/Min:", max(result), '/', min(result),)

        sys.exit()

if __name__ == '__main__':
    main()
