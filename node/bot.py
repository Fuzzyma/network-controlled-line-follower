#!/usr/bin/env python3

import socket
import time
import json
import select
from ev3con.linienverfolgung.control import MotorControl, BetterColorSensor
from .constants import DEBUG, BOT_ADDR, AP_ADDR


class TimeoutError(RuntimeError):
    pass


class Packet:
    packet = {
        "id": 0,
        "data": None,
        "ack": False,
        "time": 0,
        "type": None,
        "referer": None
    }

    @classmethod
    def create(cls, type=None, data=None, referer=None, ack=False):
        cls.packet["type"] = type
        cls.packet["data"] = data
        cls.packet["referer"] = referer
        cls.packet["id"] += 1
        cls.packet["time"] = time.time()
        cls.packet["ack"] = ack
        return cls.packet

    @classmethod
    def last(cls):
        return cls.packet


class Bot:
    def __init__(self):
        self.botCon = BOT_ADDR
        self.apCon = AP_ADDR

        # initialize sensor and motors
        # self.sensor = ev3.ColorSensor()
        self.better_sensor = BetterColorSensor(port="1")
        # self.sensor.mode = u'COL-REFLECT'

        # self.lMotor = ev3.LargeMotor('outD')
        # self.rMotor = ev3.LargeMotor('outB')

        self.mParams = {
            "left_ports": "D",
            "right_ports": "B",
            "avg_speed": 300,
            "margin_stop": 10,
            "avg_stop": 10
        }

        self.motor = MotorControl(**self.mParams)

        # setup socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(self.botCon)

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

        self.corrections = []

        self.debug = DEBUG
        self.msgCnt = 0

    def tryReceive(self, type='CONTROL'):
        readable, writable, exceptional = select.select([self.sock], [], [self.sock], 0)

        if not readable:
            return False

        try:
            payload, addr = self.sock.recvfrom(256)
        except (socket.error, socket.herror, socket.gaierror, socket.timeout):
            return False
        else:
            self.received = json.loads(payload.decode("utf-8"))

            if self.debug:
                print("Package:", self.received)

            if self.received["ack"]:
                if self.debug:
                    print("Received ACK Request. Sending Answer")
                self.send(type="ACK")

            if self.received["type"] == "STOP":
                raise KeyboardInterrupt

            if self.received["type"] == 'CONTROL':
                self.corrections.append(self.received)  # filter and sort!!!

            if self.received["type"] == 'ACK' and self.debug:
                print("Received ACK")

            if self.received["type"] != type:
                return False
            return True

    '''def checkSock(self):
        readable, writable, exceptional = select.select([self.sock], [], [self.sock])
        return not not readable
    '''

    def receive(self, type='DATA', timeout=-1):
        start = time.time()

        while not self.tryReceive(type):
            if timeout > -1 and time.time() - start > timeout/1000.0:
                raise TimeoutError
            continue

        return self

    def send(self, data=None, type='DATA', ack=False):
        # self.msgCnt += 1
        payload = Packet.create(type, data, self.received["id"], ack)

        '''payload = {
            "time": time.time(),
            "type": type,
            "data": data,
            "id": self.msgCnt,
            "referer": self.received["id"],
            "ack": ack
        }'''

        if self.debug:
            print("Sending:", payload)

        self.sock.sendto(json.dumps(payload).encode('utf-8'), self.apCon)

        return self

    def sendEnsured(self, data=None, type='CONTROL'):
        while True:
            try:
                self.send(data, type, ack=True).receive('ACK', 1000)
                break
            except TimeoutError:
                continue
        return self

    def calibrate(self):
        self.receive('CALIBRATION_REQUEST').sendEnsured(self.getCalibrationData(), 'CALIBRATION_DATA')

    def getCalibrationData(self):
        # ev3.Sound.speak('white')
        print("white:")
        input("Press Enter to continue...")
        white = self.getData()

        # ev3.Sound.speak('black')
        print("black:")
        input("Press Enter to continue...")
        black = self.getData()

        if self.debug:
            print("white: ", white)
            print("black: ", black)

        return [white, black]

    def left(self, dv):
        # self.lMotor.run_forever(speed_sp=speed)
        self.motor.set_speed(dv, self.mParams["left_ports"])
        return self

    def right(self, dv):
        # self.rMotor.run_forever(speed_sp=speed)
        self.motor.set_speed(-dv, self.mParams["right_ports"])
        return self

    def stop(self):
        self.motor.stop()
        return self

    def getData(self):
        return self.better_sensor.grey_avg
        # return self.sensor.value()

    def getLastCorrection(self):
        if self.corrections:
            return self.corrections[-1].data
        else:
            return 0

    def reset(self):
        self.motor.reset()
        return self

    '''def getSpeed(self):
        correction = self.getLastCorrection()

        left = max(-1000, min(1000, int(self.speed + correction)))
        right = max(-1000, min(1000, int(self.speed - correction)))

        return left, right'''


def main():
    b = Bot()
    b.calibrate()

    i = 0.0
    start = time.time()

    try:
        while True:
            i += 1
            # benchmark1.append(time.time())

            b.send(b.getData(), "BENCHMARK")
            try:
                dv = b.receive("BENCHMARK", timeout=50).getLastCorrection()
            except TimeoutError:
                continue
            else:
                b.left(dv).right(dv).stop()

            # benchmark2.append(time.time())

    except KeyboardInterrupt:
        b.stop()
        print("The average loop time was", (time.time() - start)/i * 1000, "ms")
        # for i in range(len(benchmark1)):
        #     if i < len(benchmark2):
        #         print((benchmark2[i] - benchmark1[i]) * 1000)

if __name__ == '__main__':
    # profile.run('main()')
    main()
