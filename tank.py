
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
# import tank_relayController
import time
# import tank_temp
import tank_cfg
import tank_log

import datetime







def setup_log():
    default_log_dir = r'/var/log/tank/'
    default_logfile = default_log_dir+r'/tank.log'

    if not os.path.exists(default_log_dir):
        os.makedirs(default_log_dir)

    logging.basicConfig(filename=default_logfile, level=logging.DEBUG,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s')



comms_file = "/mnt/ram/relay_control.txt"
def check_comms():
    if os.path.exists(comms_file):
        with open(comms_file, 'r') as f:
            data = f.read().split('\n')
        os.remove(comms_file)
        cfg = tank_cfg.Config()

        fields = data[0].split(' ')
        if 'togglerelay' in fields[0]:
            relay = fields[1]
            for r in cfg.relay_items:
                if r[tank_cfg.ITEM_NAME] == relay:
                    r[tank_cfg.ITEM_OBJECT].toggle()

        if 'setsched' in fields[0]:
            timername = fields[1]
            for timr in cfg.timer_items:
                if timr[tank_cfg.ITEM_NAME] == timername:
                    timr[tank_cfg.ITEM_OBJECT].new_schedule(
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
    tank_logger = tank_log.TankLog()

    cfg = tank_cfg.Config()

    tank_logger.init()
    for item in cfg.items:
        item[tank_cfg.ITEM_OBJECT].init()

    print ("TANK Monitor Running....")
    while True:
        time.sleep(5)
        check_comms()
        for item in cfg.items:
            item[tank_cfg.ITEM_OBJECT].tick()
        tank_logger.tick()


if __name__ == '__main__':
    main()
