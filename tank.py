
class Ticker(object):
    def __init__(self):
        self._name = ''
        self._action_interval = 120

    def init(self):
        pass

    def tick(self):
        pass

    @property
    def name(self):
        return self._name

    def time_next_action(self):
        now = datetime.datetime.now()
        secs_since_hour = (now.minute * 60) + now.second
        i = 0
        while i < secs_since_hour:
            i += self._action_interval
        r = time.time() + i - secs_since_hour
        return r

import logging
import os
import time

import cfg

import logg
import timer
import datetime


comms_file = "/mnt/ram/relay_control.txt"
status_file = "/mnt/ram/relay_status.txt"


def setup_log():
    default_log_dir = r'/var/log/tank/'
    default_logfile = default_log_dir+r'/tank.log'

    if not os.path.exists(default_log_dir):
        os.makedirs(default_log_dir)

    logging.basicConfig(filename=default_logfile, level=logging.DEBUG,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s')


def toggle_relay(name):
    while os.path.exists(comms_file):
        time.sleep(1)

    with open(comms_file, 'w') as f:
        f.write("togglerelay {name} \n".format(name=name))


def set_schedule(n, mon, tue, wed, thu, fri, sat, sun):
    with open(comms_file, 'w') as f:
        f.write("setsched {n} {m} {t} {w} {th} {f} {sa} {su} \n".
                format(n=n, m=mon, t=tue, w=wed, th=thu, f=fri, sa=sat, su=sun))


def get_relay_query(name):
    filename = ("{name}.sched".format(name=name)).replace(' ', '_')
    return "?r={name}&".format(name=name)+timer.get_query(filename)


def get_relay_state_str(name):
    try:
        with open(status_file, 'r') as f:
            lines = f.read().split('\n')

        actual = '?'
        timerr = '?'
        override = '?'
        for l in lines:
            if l.startswith(name):
                fields = l.split(' ')
                actual = fields[1]
                timerr = fields[2]
                override = fields[3]
    except IOError:
        actual = '?e'
        timerr = '?e'
        override = '?e'
    return "Actual:"+actual+"   Timer:"+timerr+"   Override:"+override


def check_comms():
    if os.path.exists(comms_file):
        with open(comms_file, 'r') as f:
            data = f.read().split('\n')
        os.remove(comms_file)
        config = cfg.Config()

        fields = data[0].split(' ')
        if 'togglerelay' in fields[0]:
            relay = fields[1]
            for r in config.relay_items:
                if r[cfg.ITEM_NAME] == relay:
                    r[cfg.ITEM_OBJECT].toggle()

        if 'setsched' in fields[0]:
            timername = fields[1]
            for timr in config.timer_items:
                if timr[cfg.ITEM_NAME] == timername:
                    timr[cfg.ITEM_OBJECT].new_schedule(
                        fields[2],
                        fields[3],
                        fields[4],
                        fields[5],
                        fields[6],
                        fields[7],
                        fields[8])


def main():
    setup_log()
    logging.info("STARTED")
    tank_logger = logg.TankLog()

    config = cfg.Config()

    tank_logger.init()
    for item in config.items:
        if item is not None:
            if cfg.ITEM_OBJECT in item:
                item[cfg.ITEM_OBJECT].init()

    print ("TANK Monitor Running....")
    while True:
        time.sleep(5)
        check_comms()
        for item in config.items:
            if item is not None:
                if cfg.ITEM_OBJECT in item:
                    item[cfg.ITEM_OBJECT].tick()
        tank_logger.tick()


if __name__ == '__main__':
    main()
