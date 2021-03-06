#!/usr/bin/env python3

import socket
import json
import time
import select
import sys


if __name__ == '__main__':
    from ev3con.linienverfolgung.pid import PID as BasePID
    from constants import DEBUG, BOT_ADDR, AP_ADDR, ShutdownException
else:
    from node.ev3con.linienverfolgung.pid import PID as BasePID
    from .constants import DEBUG, BOT_ADDR, AP_ADDR, ShutdownException


class PID(BasePID):
    def __init__(self, kp, ki=0.0, kd=0.0, white=255, black=0, **kwargs):
        BasePID.__init__(self, kp, ki, kd, **kwargs)

        try:
            self.grey_soll = 0
            # self.grey_soll = ((127.5 - black) / (white - black)) * 255
        except ZeroDivisionError:
            print("Calibration failed", file=sys.stderr)
            raise KeyboardInterrupt
        self.black = black
        self.white = white
        self.last_darkest_value = 255
        self.last_darkest_side = None
        self.threshold_white = 220

    def dv(self, grey):
        """
        Calculate needed speed change
        :param grey:
        :return: speed
        """

        try:
            grey_l = ((grey[0] - self.black) / (self.white - self.black)) * 255
            grey_r = ((grey[1] - self.black) / (self.white - self.black)) * 255
        except ZeroDivisionError:
            print("Calibration failed", file=sys.stderr)
            sys.exit()
        speed = self.calc(grey_l-grey_r, self.grey_soll)
        # speed = self.calc(grey, self.grey_soll)

        return int(speed)


class AP:
    def __init__(self, sockets=True):
        self.botCon = BOT_ADDR
        self.apCon = AP_ADDR

        if sockets:
            # setup socket
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.bind(self.apCon)

            # Use non blocking methods (program flow will not get interrupted)
            self.sock.setblocking(True)

        self.average_speed = 500

        self.received = {
            "id": 0,
            "data": None,
            "ack": False,
            "time": 0,
            "type": None,
            "referer": None,
            "last": False
        }  # data last received

        self.pid = None

        self.data = []
        self.msgCnt = 0

        self.history = {}

    # overwrite this function to receive data from elsewhere
    def receive_implementation(self):
        readable, writable, exceptional = select.select([self.sock], [], [self.sock], 0)

        if not readable:
            return False

        try:
            payload, addr = self.sock.recvfrom(256)
        except (socket.error, socket.herror, socket.gaierror, socket.timeout):
            return False
        else:
            self.received = json.loads(payload.decode("utf-8"))
            return True

    def tryReceive(self, type='CONTROL'):
        if not self.receive_implementation():
            return False

        if DEBUG >= 3:
            print("Package:", self.received)

        # Ack is handled by dispatcher now
        if self.received["ack"]:
            if DEBUG >= 3:
                print("Received ACK Request. Sending Answer")
            self.send(type="ACK")

        if self.received["type"] == 'DATA':
            self.data.append(self.received)  # filter and sort!!!

        if self.received["type"] == 'ACK' and DEBUG >= 3:
            print("Received ACK")

        if self.received["type"] == 'CALIBRATION_DATA':
            white, black = self.received["data"]
            self.pid = PID(0.2, 5, 5, white, black, antiwindup=5, maxval=500)

        if self.received["type"] == 'SHUTDOWN':
            raise ShutdownException

        if self.received["type"] != type:
            return False
        return True

    def receive(self, type='DATA', timeout=None):
        start = time.time()

        while not self.tryReceive(type):
            if timeout is not None and time.time() - start > timeout/1000.0:
                raise TimeoutError
            continue

        return self

    # overwrite this function to send data elsewhere
    def send_implementation(self, payload):
        self.sock.sendto(payload.encode('utf-8'), self.botCon)
        return self

    def send(self, data=None, type='CONTROL', ack=False, last=False):
        self.msgCnt += 1
        payload = {
            "time": time.time(),
            "type": type,
            "data": data,
            "id": self.msgCnt,
            "referer": self.received["id"],
            "ack": ack,
            "last": last
        }

        if DEBUG >= 3:
            print("Sending:", payload)

        self.history[self.msgCnt] = payload

        self.send_implementation(json.dumps(payload))

        return self

    def sendEnsured(self, data=None, type='CONTROL', timeout=None, interval=1000, last=False):
        start = time.time()

        while True:
            try:
                self.send(data, type, ack=True, last=last).receive('ACK', interval)
                break
            except TimeoutError:
                if timeout is not None and time.time() - start > timeout / 1000.0:
                    raise TimeoutError
                continue
        return self

    def calibrate(self):
        white, black = self.sendEnsured(type='CALIBRATION_REQUEST', data=False).receive('CALIBRATION_DATA').received["data"]
        # self.midpoint = (white - black) / 2 + black

        # self.pid = PID(1.4, 0.01, -5, white, black, **{"antiwindup": 20, "maxval": 300})
        # Holy grail of control parameters
        self.pid = PID(0.2, 5, 5, white, black, antiwindup=5, maxval=500)

        if DEBUG >= 3:
            print("Got calibration data: White [", white, "], Black [", black, "]")
        return self

    @property
    def last_data(self):
        if not len(self.data):
            return self.pid.grey_soll, self.pid.grey_soll
        else:
            return self.data[-1]["data"]

    def getCorrection(self):
            a = self.pid.dv(self.last_data)

            left = max(-1000, min(1000, self.average_speed + a))
            right = max(-1000, min(1000, self.average_speed - a))

            return [left, right]

    def forceStop(self):
        self.sendEnsured(type="BLACK_LINE", interval=200)
        return self

    def sendCorrection(self):
        self.send(self.getCorrection(), "CONTROL")
        return self


def main():
    ap = AP()
    try:
        print("Waiting for first package")
        ap.calibrate()

        while True:
            ap.receive("BENCHMARK").send(ap.getCorrection(), "BENCHMARK")

            # if ap.received["referer"] != 0:
            #     print "Roundtrip:", (time.time() - ap.history[ap.received["referer"]]["time"]) * 1000
    except KeyboardInterrupt:
        try:
            ap.sendEnsured(type="STOP", timeout=2000)
        except TimeoutError:
            pass
        return


if __name__ == '__main__':
    main()
