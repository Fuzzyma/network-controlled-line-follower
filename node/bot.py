#!/usr/bin/env python3

import socket
import time as base_time
import json
import select


if __name__ == '__main__':
    from MotorControl import MotorControl
    from ev3con.linienverfolgung.control import BetterColorSensor
    from constants import DEBUG, BOT_ADDR, AP_ADDR, RIGHT_PORT, LEFT_PORT
else:
    from node.ev3con.linienverfolgung.control import BetterColorSensor
    from node.MotorControl import MotorControl
    from .constants import DEBUG, BOT_ADDR, AP_ADDR, RIGHT_PORT, LEFT_PORT


class Counter:
    def __init__(self):
        self.cnt = 0

    def touch(self):
        self.cnt += 1

    def get(self):
        return self.cnt

class Benchmark:

    def __init__(self, cnt=Counter()):
        self.cnt = cnt
        self.times = {}
        self.data = {}
        self.last = []

    def add(self, key, finish=False):

        if key not in self.times:
            self.times[key] = {}

        if not finish:
            self.last = [self.cnt.get(), key, base_time.time()]
        else:
            if self.last[1] != key or self.last[0] != self.cnt.get():
                print("Something bad happend")
                return
            self.times[key][self.cnt.get()] = [self.last[2], base_time.time()]

    def calcDiff(self):

        cropped = {}
        mini = 10000000

        for i in self.times:
            self.times[i].pop(0, None)
            self.times[i].pop(1, None)
            self.times[i].pop(self.cnt.get(), None)
            # mini = min(len(cropped[i]), mini)

        #for i in cropped:
        #    cropped[i] = cropped[i][:mini]

        cropped = self.times

        self.data = {}

        a = set([])

        for key in cropped:
            for index in cropped[key]:
                a.add(index)

        minimal_time = 1000000000

        for index in a:

            self.data[index] = {}

            for key in cropped:
                try:
                    self.data[index][key] = (cropped[key][index][1] - cropped[key][index][0])*1000
                except KeyError:
                    pass

            try:
                self.data[index]["Waiting"] = (cropped["Receiving Data"][index][0] - cropped["Send Data"][index][1]) * 1000
            except KeyError:
                pass
            try:
                self.data[index]["Overall Loop time"] = (cropped["Motor right"][index][1] - cropped["Send Data"][index][0])*1000
            except KeyError:
                pass
            else:
                minimal_time = min(minimal_time, int(self.data[index]["Overall Loop time"]))

        cnt = len(a)

        loop_times = [0] * cnt
        read_sensor = [0] * cnt
        send_data = [0] * cnt
        receive_data = [0] * cnt
        waiting_data = [0] * cnt
        apply_data = [0] * cnt

        for d in self.data:
            d = self.data[d]
            loop_time = d["Overall Loop time"]
            read_sensor_time = d["Read Sensor"]
            send_data_time = d["Send Data"]
            receive_data_time = d["Receiving Data"]
            waiting_time = d["Waiting"]
            apply_data_time = d["Motor right"] + d["Motor left"]
            for key in cnt:
                if loop_time - 0.5 < key <= loop_time + 0.5:
                    loop_times[key] += 1
                    read_sensor[key] += read_sensor_time
                    send_data[key] += send_data_time
                    receive_data[key] += receive_data_time
                    waiting_data[key] += waiting_time
                    apply_data[key] += apply_data_time

        with open("result_bot_measurements_with_socket.txt", "w+") as f:
            print("ms", "\t".join(map(lambda h: '"' + h + '"', dict.keys(self.times))), sep='\t', file=f)
            for key in cnt:
                print(
                    key,
                    0 if loop_times[key] == 0 else read_sensor[key] / loop_times[key],
                    0 if loop_times[key] == 0 else send_data[key] / loop_times[key],
                    0 if loop_times[key] == 0 else receive_data[key] / loop_times[key],
                    0 if loop_times[key] == 0 else waiting_data[key] / loop_times[key],
                    0 if loop_times[key] == 0 else apply_data[key] / loop_times[key],
                    loop_times[key],
                    # 0 if loop_times[key] == 0 else packages[key]/loop_times[key],
                    sep='\t', file=f
                )

class BlackLineException(RuntimeError):
    pass


class time:
    base_remote = 0
    base_local = 0

    @classmethod
    def time(cls):
        return base_time.time() - cls.base_local + cls.base_remote

    @classmethod
    def set_base(cls, remote):
        if time.time() - remote < 0:
            cls.base_remote = remote
            cls.base_local = base_time.time()


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
    def __init__(self, benchmark=Benchmark()):
        self.botCon = BOT_ADDR
        self.apCon = AP_ADDR

        self.benchmark = benchmark

        # initialize sensor and motors
        # self.sensor = ev3.ColorSensor()
        self.better_sensor_l = BetterColorSensor(port="1")
        self.better_sensor_r = BetterColorSensor(port="4")
        # self.sensor.mode = u'COL-REFLECT'

        self.motor = MotorControl(RIGHT_PORT + LEFT_PORT)

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

        self.correction = None

        self.msgCnt = 0

    def tryReceive(self, type='CONTROL'):
        # Using select is in average as fast as using nonblocking sckets.
        # However: minimum time is about 3ms worse but maximum time is 20-30ms better
        readable, writable, exceptional = select.select([self.sock], [], [self.sock], 0)

        if not readable:
            return False

        try:
            self.benchmark.add("Receiving Data")
            payload, addr = self.sock.recvfrom(256)
            self.benchmark.add("Receiving Data", True)
        except (socket.error, socket.herror, socket.gaierror, socket.timeout):
            return False
        else:
            self.received = json.loads(payload.decode("utf-8"))

            if DEBUG >= 2:
                print("Package:", self.received)

            if self.received["ack"]:
                if DEBUG >= 2:
                    print("Received ACK Request. Sending Answer")
                self.send(type="ACK")

            if self.received["type"] == "TIME":
                time.set_base(self.received["data"])

            if self.received["type"] == "STOP":
                raise KeyboardInterrupt

            if self.received["type"] == "BLACK_LINE":
                raise BlackLineException

            if self.received["type"] == 'CONTROL' and time.time() - self.received["time"] > 0.05:
                if DEBUG:
                    print("Package dropped.", (time.time() - self.received["time"] - 0.05)*1000, 'ms late')
                return False

            if self.received["type"] == 'CONTROL':
                self.correction = self.received

            if self.received["type"] == 'ACK' and DEBUG >= 2:
                print("Received ACK")

            if self.received["type"] == 'CALIBRATION_REQUEST':
                if not self.received["data"]:
                    self.zero()
                    print("Calibrating")
                    self.sendEnsured(self.getCalibrationData(), 'CALIBRATION_DATA')

                if type == 'CALIBRATION_REQUEST':
                    return True

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

        if DEBUG >= 2:
            print("Sending:", payload)

        self.benchmark.add("Send Data")
        self.sock.sendto(json.dumps(payload).encode('utf-8'), self.apCon)
        self.benchmark.add("Send Data", True)
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

        if DEBUG:
            print("white: ", white)
            print("black: ", black)

        return [white[0], black[0]]

    def left(self, speed):
        # self.lMotor.run_forever(speed_sp=speed)
        self.benchmark.add("Motor left")
        self.motor.set_speed(speed, LEFT_PORT)
        self.benchmark.add("Motor left", True)
        return self

    def right(self, speed):
        # self.rMotor.run_forever(speed_sp=speed)
        self.benchmark.add("Motor right")
        self.motor.set_speed(speed, RIGHT_PORT)
        self.benchmark.add("Motor right", True)
        return self

    def stop(self):
        self.motor.stop()
        return self

    def zero(self):
        self.motor.set_speed(0, LEFT_PORT)
        self.motor.set_speed(0, RIGHT_PORT)
        return self

    def getData(self):
        self.benchmark.add("Read Sensor")
        temp = self.better_sensor_l.grey_avg, self.better_sensor_r.grey_avg
        self.benchmark.add("Read Sensor", True)
        return temp
        # return self.sensor.value()

    def getLastCorrection(self):
        if self.correction is not None:
            return self.correction["data"]
        else:
            return [0, 0]

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

    # two possible outcomes:
    # AP has data and sends request with data = True
    # AP has no data and sends request with data = False
    # In any case we have to wait for it to start
    b.receive("CALIBRATION_REQUEST")

    i = 0.0
    start = time.time()

    try:
        while True:
            i += 1
            # benchmark1.append(time.time())

            b.send(b.getData(), "BENCHMARK")
            try:
                speed_left, speed_right = b.receive("BENCHMARK", timeout=50).getLastCorrection()
            except TimeoutError:
                continue
            else:
                b.left(speed_left).right(speed_right).stop()

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
