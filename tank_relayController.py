#!/usr/bin/python

import mydebug
import threading
import time
import os
import logging


comms_file = "/mnt/ram/relay_control.txt"
status_file = "/mnt/ram/relay_status.txt"

if mydebug.RELAY_TEST == 0:
    import RPi.GPIO as GPIO
    GOUT = GPIO.OUT
    GLOW = GPIO.LOW
    GHIGH = GPIO.HIGH
    GBOARD = GPIO.BOARD
else:
    GOUT = 0
    GLOW = 0
    GHIGH = 0
    GBOARD = 0

import timer


states = ['OFF', 'ON']


def setmode(n):
    if mydebug.RELAY_TEST == 0:
        GPIO.setmode(n)


def cleanup():
    if mydebug.RELAY_TEST == 0:
        GPIO.cleanup()


def setup(a, b):
    if mydebug.RELAY_TEST == 0:
        GPIO.setup(a, b)


def output(a, b):
    if mydebug.RELAY_TEST == 0:
        GPIO.output(a, b)


class Controller(object):
    def __init__(self):
        self.relays = Relays()
        self.relay0 = self.relays.get_relay(0)
        self.relay1 = self.relays.get_relay(1)
        self.relay2 = self.relays.get_relay(2)
        self.relay3 = self.relays.get_relay(3)

        # self.schedule1 = timer.Schedule2("timer0.sched")
        # self.schedule2 = timer.Schedule2("timer1.sched")

        self.timers = []

        self._stop = False

    def init_timers(self):
        self.timers.append(timer.Timer2(timer.Schedule2("timer0.sched"), self.relay0))
        self.timers.append(timer.Timer2(timer.Schedule2("timer1.sched"), self.relay1))
        self.timers.append(timer.Timer2(timer.Schedule2("timer2.sched"), self.relay2))
        self.timers.append(timer.Timer2(timer.Schedule2("timer3.sched"), self.relay3))

        for t in self.timers:
            t.start()

        # self.t1.start()
        #
        # self.t2 = timer.Timer2(self.schedule2, self.relay1)
        # self.t2.start()

        thread = threading.Thread(target=self.task)
        thread.start()

    def running(self):
        return (not self._stop) or self.t1.running() or self.t2.running()

    def task(self):
        while not self._stop:
            for _ in range(5):
                if not self._stop:
                    time.sleep(1)

            if not self._stop:
                if os.path.exists(comms_file):
                    with open(comms_file, 'r') as f:
                        data = f.read().split('\n')
                    os.remove(comms_file)
                    fields = data[0].split(' ')
                    if 'togglerelay' in fields[0]:
                        relay = int(fields[1])
                        self._toggle(relay)
                    if 'setsched' in fields[0]:
                        relay = int(fields[1])
                        self._set_sched(relay, fields[2],fields[3],fields[4],fields[5],fields[6],fields[7],fields[8])

            if not self._stop:
                with open(status_file, 'w') as f:
                    for n in range(4):
                        r, t, o = self._get_relay_state(n)
                        f.write("relay{n} {r} {t} {o}\n".format(n=n, r=states[r], t=states[t], o=states[o]))
                # r, t, o = self._get_relay_state(1)
                # status1 = "relay1 {r} {t} {o}\n".format(r=states[r], t=states[t], o=states[o])

        logging.warn("Relay controller stopped")
        self._stop = True

    def _get_relay_state(self, n):
        return self.relays.get_relay(n).state()

    def _toggle(self, n):
        r = self.relays.get_relay(n)
        actual_state, tstate, ostate = r.state()
        if actual_state == 1:
            r.turn_relay_off()
        else:
            r.turn_relay_on()

    def _set_sched(self, relay, a,b,c,d,e,f,g):
        self.timers[relay].new_schedule(a,b,c,d,e,f,g)

    def stop(self):
        self._stop = True
        for t in self.timers:
            t.stop()
        self.relays.cleanup()


def toggle_relay(n):
    while os.path.exists(comms_file):
        time.sleep(1)

    with open(comms_file, 'w') as f:
        f.write("togglerelay {n} \n".format(n=n))


def set_schedule(n, mon, tue, wed, thu, fri, sat, sun):
    with open(comms_file, 'w') as f:
        f.write("setsched {n} {m} {t} {w} {th} {f} {sa} {su} \n".format(n=n,m=mon,t=tue,w=wed,th=thu,f=fri,sa=sat,su=sun))


def get_relay_query(n):
    if n == 0:
        return timer.get_query("timer0.sched")
    if n == 1:
        return timer.get_query("timer1.sched")
    if n == 2:
        return timer.get_query("timer2.sched")
    if n == 3:
        return timer.get_query("timer3.sched")


def get_relay_state_str(n):

    with open(status_file, 'r') as f:
        lines = f.read().split('\n')

    fields = lines[n].split(' ')

    actual = fields[1]
    timerr = fields[2]
    override = fields[3]
    return "Actual:"+actual+"   Timer:"+timerr+"   Override:"+override


class Relays(object):
    def __init__(self):
        self.pinList = [11, 13, 15, 16]
        setmode(GBOARD)

        self.relays = []

        self.relays.append(Relay(0, self.pinList[0]))
        self.relays.append(Relay(1, self.pinList[1]))
        self.relays.append(Relay(2, self.pinList[2]))
        self.relays.append(Relay(3, self.pinList[3]))

    def get_relay(self, n):
        return self.relays[n]

    @classmethod
    def cleanup(cls):
        cleanup()


class Relay(object):
    def __init__(self, new_id, pin):
        self.id = new_id
        self.pin = pin
        self.current_state = 0
        self.timer_state = 0
        setup(self.pin, GOUT)
        self.turn_relay_off()
        self.override = 0

    def turn_relay_on(self):
        logging.info(str(self.id)+" ON")
        output(self.pin, GLOW)
        self.current_state = 1

    def turn_relay_off(self):
        logging.info(str(self.id)+" OFF")
        output(self.pin, GHIGH)
        self.current_state = 0

    def set_state(self, new_state):
        # print "{id} {state}".format(id=self.id, state=new_state)
        if new_state:
            self.timer_state = 1
            if not self.override:
                self.turn_relay_on()
        else:
            self.timer_state = 0
            if not self.override:
                self.turn_relay_off()
        self.override = (self.current_state != new_state)

    # def toggle_override(self):
    #     if self.override == 0:
    #         self.override = 1
    #     else:
    #         self.override = 0

    def state(self):
        return self.current_state, self.timer_state, self.override


def setup_log():
    default_log_dir = r'/var/log/tank/'
    default_logfile = default_log_dir+r'/relay.log'

    if not os.path.exists(default_log_dir):
        os.makedirs(default_log_dir)

    logging.basicConfig(filename=default_logfile, level=logging.DEBUG,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s')


def main():
    setup_log()
    logging.info("STARTED")
    controller = Controller()
    controller.init_timers()
    try:
        while controller.running():
            time.sleep(60)
    except KeyboardInterrupt:
        print "\nQUITTING\n"
        logging.warn("Ctrl-C")
        while controller.running():
            controller.stop()
            time.sleep(0.1)


if __name__ == "__main__":
    main()


# # init list with pin numbers
#
# #pinList = [2, 3, 4, 17, 27, 22, 10, 9]
#
#
#
# # loop through pins and set mode and state to 'low'
#
# for i in pinList:
#     GPIO.setup(i, GPIO.OUT)
#     GPIO.output(i, GPIO.HIGH)
#
# # time to sleep between operations in the main loop
#
# SleepTimeL = 1.0
# SleepTimeH = 10.0
#
# # main loop
#
# try:
#    count = 999
#    while (count > 0):
#
#       print '   The count is:', count
#       time.sleep(SleepTimeH);
#
#       for i in pinList:
#          GPIO.output(i, GPIO.LOW)
#          time.sleep(SleepTimeL);
#
#       pinList.reverse()
#
#       for i in pinList:
#          GPIO.output(i, GPIO.HIGH)
#          time.sleep(SleepTimeL);
#
#       time.sleep(SleepTimeH);
#
#       pinList.reverse()
#       count = count - 1
#
#
# # End program cleanly with keyboard
# except KeyboardInterrupt:
#   print "  Quit"
#
#   # Reset GPIO settings
#   GPIO.cleanup()


# find more information on this script at
# http://youtu.be/oaf_zQcrg7g
