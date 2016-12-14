#!/usr/bin/env python3

from node.piped import Piped
import socket
import json


def main():
    p = Piped()

    # setup socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # self.sock.bind(AP_ADDR)

    # Use blocking methods
    sock.setblocking(True)

    while not p.closed:
        if p.empty():
            continue

        while not p.empty():
            msg = p.pullJSON()

            # Dont handle this package. Pipe it to next process
            if msg["type"] != 'DATA':
                p.pushJSON(msg["answer"])
                continue

            sock.sendto(json.dumps(msg["answer"]).encode('utf8'), ('192.168.1.121', 45602))
            p.repush(msg)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
