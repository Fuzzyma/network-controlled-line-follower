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
        "answer": None,
        "last": False
    }

    clean_ = {
        "id": 0,
        "data": None,
        "ack": False,
        "time": 0,
        "type": None,
        "referer": None,
    }

    id = 0

    def __init__(self, type=None, data=None, referer=None, ack=False, answer=None):
        self.package["type"] = type
        self.package["data"] = data
        self.package["referer"] = referer
        self.package["id"] += 1
        self.package["time"] = time.time()
        self.package["ack"] = ack
        self.package["answer"] = answer

    @classmethod
    def clean(cls, package):
        for i in package:
            if i in cls.clean_:
                cls.clean_[i] = package[i]

        cls.id += 1
        cls.clean_["id"] = cls.id
        return cls.clean_
