IN = 0
OUT = 0
LOW = 0
HIGH = 0
BOARD = 0
BCM = 0
RISING = 0
FALLING = 0
BOTH = 0

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


def add_event_detect(a, b):
    global _sink
    _sink = str(a)+str(b)


def add_event_callback(a, b):
    global _sink
    _sink = str(a) + str(b)


def remove_event_detect(a):
    return a
