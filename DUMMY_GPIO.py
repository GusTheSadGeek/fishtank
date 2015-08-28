IN = 0
OUT = 0
LOW = 0
HIGH = 0
BOARD = 0
BCM = 0


_sink = 0


def setwarnings(a):
    global _sink
    _sink = a


def setmode(a):
    global _sink
    _sink = a


def setup(a, b):
    global _sink
    _sink = str(a)+str(b)


def output(a, b):
    global _sink
    _sink = str(a)+str(b)


def cleanup(a):
    global _sink
    _sink = a


def input(a):
    return a
