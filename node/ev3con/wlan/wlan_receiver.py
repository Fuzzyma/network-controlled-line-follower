import sys, argparse, socket

parser = argparse.ArgumentParser(sys.argv[0])
parser.add_argument("-ip", dest="LISTEN_IP", type=str, default="0.0.0.0")
parser.add_argument("-port", dest="LISTEN_PORT", type=float, default=5005)
args = parser.parse_args(sys.argv[1:])

sock = socket.socket(type=socket.SOCK_DGRAM)
sock.bind((args.LISTEN_IP,args.LISTEN_PORT))

print "Empfang wird gestartet"

try:
    while True:
        data, addr = sock.recvfrom(1024)
        print data + " " + str(addr)
except (KeyboardInterrupt, SystemExit):
    sock.close()
    print "Programm wird beendet"
