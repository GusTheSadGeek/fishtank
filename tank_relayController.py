#!/usr/bin/python

import mydebug
import threading
import time
import os
import logging
import tank_temp as temperature
import tank_cfg

comms_file = "/mnt/ram/relay_control.txt"
status_file = "/mnt/ram/relay_status.txt"
pin_file = "relay_pins.conf"

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
        self._cfg = tank_cfg.Config()
        self.relays = Relays()
        tank_cfg.Instances().relays = self.relays

        self.timers = []
        tank_cfg.Instances().timers = self.timers

        self._stop = False

    def init_timers(self):
        cfg = tank_cfg.Config()
        for t in cfg.timers:
            filename = (t['name']+'.sched').replace(' ', '_')
            self.timers.append( timer.Timer2(t, timer.Schedule2(filename)) )
        #
        # for n in range(self.relays.count):
        #     filename = "timer{n}.sched".format(n=n)
        #     self.timers.append(timer.Timer2(timer.Schedule2(filename), self.relays.get_relay(n)))

        for t in self.timers:
            t.start()

        thread = threading.Thread(target=self.task)
        thread.start()

    @property
    def running(self):
        for t in self.timers:
            if not t.running:
                return False
        return not self._stop

    def task(self):
        count = 0
        while not self._stop:
            for _ in range(5):
                if not self._stop:
                    time.sleep(1)

            count += 1
            if count > 12:
                count = 0
                for r in self.relays.relays:
                    if r.controlledby_temp:
                        temp = temperature.get_current_temp(r.controller)
                        logging.info("{r} {t} {temp}".format(r=r.id, t=r.controller, temp=temp))
                        if temp > r.on_temp:
                            r.turn_relay_on()
                        if temp < r.off_temp:
                            r.turn_relay_off()

            if not self._stop:
                if os.path.exists(comms_file):
                    with open(comms_file, 'r') as f:
                        data = f.read().split('\n')
                    os.remove(comms_file)
                    fields = data[0].split(' ')
                    if 'togglerelay' in fields[0]:
                        relay = fields[1]
                        self._toggle(relay)
                    if 'setsched' in fields[0]:
                        relay = fields[1]
                        self._set_sched(relay,
                                        fields[2],
                                        fields[3],
                                        fields[4],
                                        fields[5],
                                        fields[6],
                                        fields[7],
                                        fields[8])

            if not self._stop:
                with open(status_file, 'w') as f:
                    for relay in self.relays.relays:
                        r, t, o = relay.state()
                        f.write("{n} {r} {t} {o}\n".format(n=relay.id, r=states[r], t=states[t], o=states[o]))
                # r, t, o = self._get_relay_state(1)
                # status1 = "relay1 {r} {t} {o}\n".format(r=states[r], t=states[t], o=states[o])

        logging.warn("Relay controller stopped")
        self._stop = True

    def _get_relay_state(self, n):
        return self.relays.get_relay(n).state()

    def _toggle(self, id):
        r = self.relays.get_relay(id)
        actual_state, tstate, ostate = r.state()
        if actual_state == 1:
            r.turn_relay_off()
        else:
            r.turn_relay_on()

    def _set_sched(self, relay, a, b, c, d, e, f, g):
        for t in self.timers:
            if t.controls == relay:
                t.new_schedule(a, b, c, d, e, f, g)

    def stop(self):
        if not self._stop:
            print "Stopping Timers"
            self._stop = True
            for t in self.timers:
                t.stop()
            print "Timers stopped"
            self.relays.cleanup()
            print "Cleaning up Relays"


def toggle_relay(id):
    while os.path.exists(comms_file):
        time.sleep(1)

    with open(comms_file, 'w') as f:
        f.write("togglerelay {id} \n".format(id=id))


def set_schedule(n, mon, tue, wed, thu, fri, sat, sun):
    with open(comms_file, 'w') as f:
        f.write("setsched {n} {m} {t} {w} {th} {f} {sa} {su} \n".
                format(n=n, m=mon, t=tue, w=wed, th=thu, f=fri, sa=sat, su=sun))


def get_relay_query(id):
    filename = ("{id}.sched".format(id=id)).replace(' ', '_')
    return "?r={id}&".format(id=id)+timer.get_query(filename)


def get_relay_state_str(id):
    try:
        with open(status_file, 'r') as f:
            lines = f.read().split('\n')

        actual = '?'
        timerr = '?'
        override = '?'
        for l in lines:
            if l.startswith(id):
                fields = l.split(' ')
                actual = fields[1]
                timerr = fields[2]
                override = fields[3]
    except IOError:
        actual = '?e'
        timerr = '?e'
        override = '?e'
    return "Actual:"+actual+"   Timer:"+timerr+"   Override:"+override


class Relays(object):
    def __init__(self):
        cfg = tank_cfg.Config()

        setmode(GBOARD)
        self._relays = []

        for r in cfg._relays:
            self._relays.append(Relay(r))

    @property
    def count(self):
        return len(self._relays)

    @property
    def relays(self):
        return self._relays

    # @staticmethod
    # def load_pins():
    #     with open(pin_file) as f:
    #         pins = f.read().strip().split('\n')
    #     return map(int, pins)

    # def get_relay(self, n):
    #     if len(self._relays) > n:
    #         return self._relays[n]
    #     return None

    def get_relay(self, id):
        for r in self._relays:
            if r.id == id:
                return r
        return None

    @classmethod
    def cleanup(cls):
        cleanup()


class RelayState:
    OFF = 0
    ON = 1
    FOFF = 2
    FON = 3
    UNKNOWN = 4

    @classmethod
    def toString(cls,n):
        if n == cls.OFF:
            return 'OFF'
        if n == cls.ON:
            return 'ON'
        if n == cls.FOFF:
            return 'FORCED OFF'
        if n == cls.FON:
            return 'FORCED ON'
        return 'UNKNOWN'


class Relay(object):
    def __init__(self, cfg):
        self.id = cfg['name']
        self.pin = cfg['pin']
        self.controller = cfg['controller']
        self.controlledby_temp = False
        self.on_temp = None
        self.off_temp = None

        if 'none' not in self.controller:
            for t in tank_cfg.Instances().temps:
                if self.controller in t.name:
                    self.controlledby_temp = True
                    self.on_temp = cfg['ontemp']
                    self.off_temp = cfg['offtemp']

        self.current_state = RelayState.UNKNOWN
        self.timer_state = 0
        setup(self.pin, GOUT)
        self.turn_relay_off()
        self.override = 0

    def turn_relay_on(self):
        if self.current_state != RelayState.ON:
            logging.info(str(self.id)+" ON")
        output(self.pin, GLOW)
        self.current_state = RelayState.ON

    def turn_relay_off(self):
        if self.current_state != RelayState.OFF:
            logging.info(str(self.id)+" OFF")
        output(self.pin, GHIGH)
        self.current_state = RelayState.OFF

    def force_relay_on(self):
        if self.current_state != RelayState.FON:
            logging.info(str(self.id)+" FON")
        output(self.pin, GLOW)
        self.current_state = RelayState.FON

    def force_relay_off(self):
        if self.current_state != RelayState.FOFF:
            logging.info(str(self.id)+" FOFF")
        output(self.pin, GHIGH)
        self.current_state = RelayState.FOFF

    def unforce_relay(self):
        if self.current_state == RelayState.FOFF:
            logging.info(str(self.id)+" OFF")
            output(self.pin, GLOW)
            self.current_state = RelayState.OFF
        if self.current_state == RelayState.FON:
            logging.info(str(self.id)+" ON")
            output(self.pin, GHIGH)
            self.current_state = RelayState.ON

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
