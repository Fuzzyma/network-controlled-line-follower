#!/usr/bin/env python3

from optparse import OptionParser

parser = OptionParser()
parser.add_option("-p", "--file", dest="filename",
                  help="write report to FILE", metavar="FILE")
parser.add_option("-q", "--quiet",
                  action="store_false", dest="verbose", default=True,
                  help="don't print status messages to stdout")

(options, args) = parser.parse_args()


def addFunction(args, options):
    removeFunction(args, options)

    filename = args[0]
    priority = args[1]

    with open('network_functions.txt', 'a', encoding='utf8') as f:
        f.write(filename + '\t' + priority + '\n')


def removeFunction(args, options):

    filename = args[0]

    with open('network_functions.txt', 'r+', encoding='utf8') as f:
        d = f.readlines()
        f.seek(0)
        for i in d:
            if i.rstrip('\n').split('\t')[0] != filename:
                f.write(i)

        f.truncate()
        f.close()



commands = {
    "add": addFunction,
    "rm": removeFunction
}


if args[0] in commands:
    commands[args[0]](args[1:], options)
