#!/usr/bin/env python3

import time


class Package:
    package = {
        "id": 0,
        "data": None,
        "ack": False,
        "time": 0,
        "type": None,
        "referer": None,
        "answer": None
    }

    def __init__(self, type=None, data=None, referer=None, ack=False, answer=None):
        self.package["type"] = type
        self.package["data"] = data
        self.package["referer"] = referer
        self.package["id"] += 1
        self.package["time"] = time.time()
        self.package["ack"] = ack
        self.package["answer"] = answer

