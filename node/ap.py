#!/usr/bin/env python3

import socket
import json
import time
import select

if __name__ == '__main__':
    from ev3con.linienverfolgung.pid import PID as BasePID
    from constants import DEBUG, BOT_ADDR, AP_ADDR
else:
    from node.ev3con.linienverfolgung.pid import PID as BasePID
    from .constants import DEBUG, BOT_ADDR, AP_ADDR


class TimeoutError(RuntimeError):
    pass


class BlackLineException(RuntimeError):
    pass


class PID(BasePID):
    def __init__(self, kp, ki=0.0, kd=0.0, white=255, black=0, **kwargs):
        BasePID.__init__(self, kp, ki, kd, **kwargs)

        try:
            self.grey_soll = 0
            # self.grey_soll = ((127.5 - black) / (white - black)) * 255
        except ZeroDivisionError:
            print("Caliration failed")
            raise KeyboardInterrupt
        self.black = black
        self.white = white
        self.last_darkest_value = 255
        self.last_darkest_side = None
        self.threshold_white = 220

    def dv(self, grey):
        """noetige Geschwindigkeitsaenderung"""

        try:
            grey_l = ((grey[0] - self.black) / (self.white - self.black)) * 255
            grey_r = ((grey[1] - self.black) / (self.white - self.black)) * 255

            grey = (grey_l + grey_r) / 2
            if grey < 20:
                print("Black line detected. Stop motors immediately")
                raise BlackLineException

            '''
            if grey[0] < self.last_darkest_value:
                self.last_darkest_value = grey[0]
                self.last_darkest_side = 'left'

            if grey[1] < self.last_darkest_value:
                self.last_darkest_value = grey[1]
                self.last_darkest_side = 'right'

            # print(grey_l, grey_r)

            if grey > self.threshold_white:
                print("White detected")
                if self.last_darkest_side == 'left':
                    grey_l += 30
                elif self.last_darkest_side == 'right':
                    grey_r += 30
            '''
        except ZeroDivisionError:
            print("Calibration failed")
            raise KeyboardInterrupt
        speed = self.calc(grey_l-grey_r, self.grey_soll)
        # speed = self.calc(grey, self.grey_soll)

        return int(speed)


class AP:
    def __init__(self):
        self.botCon = BOT_ADDR
        self.apCon = AP_ADDR

        # setup socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(self.apCon)

        # Use non blocking methods (program flow will not get interrupted)
        self.sock.setblocking(True)

        self.speed = 500
        self.received = {
            "id": 0,
            "data": None,
            "ack": False,
            "time": 0,
            "type": None,
            "referer": None
        }  # data last received

        self.pid = None  # PID(1.4, 0.01, -5)

        self.data = []

        self.debug = DEBUG
        self.msgCnt = 0

        self.midpoint = 127.5

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

        if self.debug:
            print("Package:", self.received)

        if self.received["ack"]:
            if self.debug:
                print("Received ACK Request. Sending Answer")
            self.send(type="ACK")

        if self.received["type"] == 'DATA':
            self.data.append(self.received)  # filter and sort!!!

        if self.received["type"] == 'ACK' and self.debug:
            print("Received ACK")

        if self.received["type"] != type:
            return False
        return True

    '''def checkSock(self):
        readable, writable, exceptional = select.select([self.sock], [], [self.sock])
        return not not readable
    '''

    def receive(self, type='DATA', timeout=None):
        start = time.time()

        while not self.tryReceive(type):
            if timeout is not None and time.time() - start > timeout/1000.0:
                raise TimeoutError
            continue

        return self

    # overwrite this function to send data elsewhere
    def send_implementation(self, payload):
        self.sock.sendto(json.dumps(payload).encode('utf-8'), self.botCon)
        return self

    def send(self, data=None, type='CONTROL', ack=False):
        self.msgCnt += 1
        payload = {
            "time": time.time(),
            "type": type,
            "data": data,
            "id": self.msgCnt,
            "referer": self.received["id"],
            "ack": ack
        }

        if self.debug:
            print("Sending:", payload)

        self.history[self.msgCnt] = payload

        # self.sock.sendto(json.dumps(payload).encode('utf-8'), self.botCon)

        self.send_implementation(json.dumps(payload).encode('utf-8'))

        return self

    def sendEnsured(self, data=None, type='CONTROL', timeout=None, interval=1000):
        start = time.time()

        while True:
            try:
                self.send(data, type, ack=True).receive('ACK', interval)
                break
            except TimeoutError:
                if timeout is not None and time.time() - start > timeout / 1000.0:
                    raise TimeoutError
                continue
        return self

    def calibrate(self):
        white, black = self.sendEnsured(type='CALIBRATION_REQUEST').receive('CALIBRATION_DATA').received["data"]
        # self.midpoint = (white - black) / 2 + black

        # self.pid = PID(1.4, 0.01, -5, white, black, **{"antiwindup": 20, "maxval": 300})
        # Holy grail of control parameters
        self.pid = PID(0.2, 5, 5, white, black, antiwindup=5, maxval=500)

        if self.debug:
            print("Got calibration data: White [", white, "], Black [", black, "]")
        return self

    @property
    def last_correction(self):
        if not len(self.data):
            return self.pid.grey_soll, self.pid.grey_soll
        else:
            return self.data[-1]["data"]

    def getCorrection(self):
        try:
            a = self.pid.dv(self.last_correction)
        except BlackLineException:
            self.forceStop()
        else:
            return a

    def forceStop(self):
        self.sendEnsured(type="BLACK_LINE", interval=200)
        return self
        '''
        # now = time.time()
        # filter all values which are older than 50ms and sort entries with time
        # sensor_data = [data for data in sensor_data if (now - data.time)*1000 < 50]
        '''

        '''
        integral = 0
        derivative = 0
        lasterror = 0
        error = 0

        # sort sensor data and use only last 20 values to calculate new control parameters
        sorted(self.data, key=lambda k: k['time'])
        self.data = self.data[-20:]

        # calculate new control parameters

        cnt = 0

        # get start parameters from last time
        for cnt, data in enumerate(self.data):
            try:
                # we found parameters
                integral = data["integral"]
                derivative = data["derivative"]
                lasterror = data["lasterror"]
                break
            except KeyError:
                continue

        # i equals the sensor data where we will start calculating so clamp the list
        if cnt != len(self.data) - 1:
            self.data = self.data[cnt + 1:]

        for cnt, data in enumerate(self.data):
            error = self.midpoint - data["data"]
            integral += error
            integral = min(50, max(integral, -50))
            derivative = error - lasterror
            lasterror = error

            self.data[cnt]["integral"] = integral
            self.data[cnt]["derivative"] = derivative
            self.data[cnt]["lasterror"] = lasterror

        correction = self.kp * error + self.ki * integral + self.kd * derivative

        # print "Error: ", error
        # print "Integral: ", integral
        # print "Derivative: ", derivative

        return correction
        '''

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
