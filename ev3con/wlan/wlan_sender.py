import sys, argparse, socket

parser = argparse.ArgumentParser(sys.argv[0])
parser.add_argument("-ip", dest="DEST_IP", type=str, default="127.0.0.1")
parser.add_argument("-port", dest="DEST_PORT", type=float, default=5005)
parser.add_argument("-m", dest="MESSAGE", type=str, default="spameggsausageandspam")
args = parser.parse_args(sys.argv[1:])

sock = socket.socket(type=socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
sock.sendto(args.MESSAGE, (args.DEST_IP,args.DEST_PORT))
sock.close()
