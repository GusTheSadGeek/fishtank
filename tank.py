
class Ticker(object):
    def __init__(self):
        self._action_interval = 120

    def init(self):
        pass

    def tick(self):
        pass

    def time_next_action(self, interval=None):
        if interval is None:
            interval = self._action_interval
        now = datetime.datetime.now()
        secs_since_hour = (now.minute * 60) + now.second
        i = 0
        while i < secs_since_hour:
            i += interval
        r = time.time() + i - secs_since_hour
        return r


import traceback
import logging
import os
import time

import cfg

import logg
import timer
import datetime
import watchdog

comms_file = "/mnt/ram/relay_control.txt"
status_file = "/mnt/ram/relay_status.txt"

loglevel = logging.WARNING
loglevel = logging.DEBUG

def setup_log():
    default_log_dir = r'/var/log/tank/'
    default_logfile = default_log_dir+r'/tank.log'

    if not os.path.exists(default_log_dir):
        os.makedirs(default_log_dir)

    logging.basicConfig(filename=default_logfile, level=loglevel,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s')


def set_log_level():
    global loglevel
    if loglevel != cfg.Config().log_level:
        loglevel = cfg.Config().log_level
        setup_log()


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
        # if 'control' in fields[0]:
        #     if 'OFF' in fields[1]:
        #         config.control_state = 'OFF'
        #     else:
        #         config.control_state = 'ACTIVE'

        # if 'configure' in fields[0]:
        #     config.water_height = fields[1]
        #     config.water_temp = fields[2]

        if 'togglerelay' in fields[0]:
            relay = fields[1]
            for r in config.relay_items:
                if r.name == relay:
                    r.object.toggle()

        if 'setsched' in fields[0]:
            timername = fields[1]
            for timr in config.timer_items:
                if timr.name == timername:
                    timr.object.new_schedule(
                        fields[2],
                        fields[3],
                        fields[4],
                        fields[5],
                        fields[6],
                        fields[7],
                        fields[8])


def main():
    setup_log()
    watchdog.start_watchdog()
    error_count = 0
    try:
        logging.warning("STARTED")
        tank_logger = logg.TankLog()

        config = cfg.Config()

        logging.warning("Current control state = {s}".format(s=config.control_state))

        tank_logger.init()
        for item in config.items:
            if item is not None:
                if item.object is not None:
                    item.object.init()

        print ("TANK Monitor Running....")
        while True:
            set_log_level()  # Only does anything if the log level has been adjusted
            time.sleep(5)
            watchdog.still_alive()
            try:
                config.tick()
                check_comms()
                for item in config.items:
                    if item is not None:
                        if item.object is not None:
                            watchdog.set_debug_info(item.object.config.name)
                            item.object.tick()
                watchdog.set_debug_info('tank_logger')
                tank_logger.tick()
                watchdog.set_debug_info('None')
                if error_count > 0:
                    error_count -= 1
            except RuntimeError as e:
                error_count += 10
                print e
                print traceback.format_exc()
                logging.critical(e)
                logging.critical(traceback.format_exc())
            except Exception as e:
                error_count += 1
                print e
                print traceback.format_exc()
                logging.critical(e)
                logging.critical(traceback.format_exc())
            if error_count > 30:
                logging.fatal('Error Count > 30 - rebooting')
                time.sleep(1)
                os.system('reboot')
    except KeyboardInterrupt as e:
        watchdog.stop_watchdog()
        print e
        print traceback.format_exc()
        logging.fatal(e)
        logging.fatal(traceback.format_exc())
        logging.fatal('PROGRAM EXITING - Ctrl C')

    except Exception as e:
        print e
        print traceback.format_exc()
        logging.fatal(e)
        logging.fatal(traceback.format_exc())
        logging.fatal('PROGRAM EXITING !!!!')


if __name__ == '__main__':
    main()
