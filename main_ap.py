from node.ap import AP, TimeoutError


def main():
    ap = AP()
    try:
        print "Requesting Calibration"
        ap.calibrate()

        while True:
            ap.receive("DATA").send(ap.getCorrection(), "CONTROL")
    except KeyboardInterrupt:
        try:
            ap.sendEnsured(type="STOP", timeout=2000)
        except TimeoutError:
            pass
        return


if __name__ == '__main__':
    main()
