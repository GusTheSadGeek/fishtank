#!/usr/bin/python

import tank_debug
import logging
import tank_cfg
import tank_log

# comms_file = "/mnt/ram/relay_control.txt"
# status_file = "/mnt/ram/relay_status.txt"


if tank_debug.RELAY_TEST == 0:
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



states = ['OFF', 'ON']


def setmode(n):
    if tank_debug.RELAY_TEST == 0:
        GPIO.setmode(n)


def cleanup():
    if tank_debug.RELAY_TEST == 0:
        GPIO.cleanup()


def setup(a, b):
    if tank_debug.RELAY_TEST == 0:
        GPIO.setup(a, b)


def output(a, b):
    if tank_debug.RELAY_TEST == 0:
        GPIO.output(a, b)




class RelayState:
    OFF = 0
    ON = 1
    FOFF = 2
    FON = 3
    UNKNOWN = 4

    @classmethod
    def toString(cls, n):
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
        self.id = cfg[tank_cfg.ITEM_NAME]
        self.pin = cfg[tank_cfg.ITEM_NAME]
        self.controlledby = cfg[tank_cfg.ITEM_CONTROLLEDBY]
        self.controller = None
        self._logger = tank_log.TankLog()
        self.on_temp = cfg[tank_cfg.ITEM_ONVAL]
        self.off_temp = cfg[tank_cfg.ITEM_OFFVAL]
#        self.old_log_stamp = time.time()
        self.avg = []
        self.moving_total = 0.0
        self.controller_state = 99

        # if 'none' not in self.controller:
        #     for t in tank_cfg.Instances().temps:
        #         if self.controller in t.name:
        #             self.controlledby_temp = True
        #             self.on_temp = cfg['ontemp']
        #             self.off_temp = cfg['offtemp']

        self.current_state = RelayState.UNKNOWN
        # self.timer_state = 0
        self.override = 0

    def init(self):
        if self.controlledby is not None:
            self.controller = tank_cfg.Config().get_item(self.controlledby)
        setup(self.pin, GOUT)
        self.turn_relay_off()

    def tick(self):
        new_state = self.controller.get_new_relay_state(self.on_temp, self.off_temp)
        if new_state == 1:
            self.set_state(True)
        if new_state == -1:
            self.set_state(False)
        if self.current_state == RelayState.ON or self.current_state == RelayState.FON:
            new_val = 5
        else:
            new_val = 0
        self.avg.append(new_val)
        if len(self.avg) > 720:
            old_val = self.avg.pop(0)
            self.moving_total -= old_val
        self.moving_total += new_val

        avg = (self.moving_total / (len(self.avg)*5)) * 100

        self._logger.log_value(self.id,
            "{avg:4.1f}".format(avg=avg), "{current}".format(current=RelayState.toString(self.current_state)))


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
        if self.controller_state == 1:
            self.current_state = RelayState.ON
            logging.info(str(self.id)+" ON")
        else:
            self.current_state = RelayState.FON

    def force_relay_off(self):
        if self.current_state != RelayState.FOFF:
            logging.info(str(self.id)+" FOFF")
        output(self.pin, GHIGH)
        if self.controller_state == 0:
            self.current_state = RelayState.OFF
            logging.info(str(self.id)+" OFF")
        else:
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
            if self.controller_state != 1:
                self.controller_state = 1
                if not self.override:
                    self.turn_relay_on()
        else:
            if self.controller_state != 0:
                self.controller_state = 0
                if not self.override:
                    self.turn_relay_off()
        self.override = (self.current_state != new_state)

    def state(self):
        return self.current_state, self.controller_state, self.override

    def toggle(self):
        if self.current_state == RelayState.ON or self.current_state == RelayState.FON:
            self.force_relay_off()
        else:
            self.force_relay_on()
        self.tick()

#
# def setup_log():
#     default_log_dir = r'/var/log/tank/'
#     default_logfile = default_log_dir+r'/relay.log'
#
#     if not os.path.exists(default_log_dir):
#         os.makedirs(default_log_dir)
#
#     logging.basicConfig(filename=default_logfile, level=logging.DEBUG,
#                         format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
#
#
# def main():
#     setup_log()
#     logging.info("STARTED")
#     controller = Controller()
#     controller.init_timers()
#     try:
#         while controller.running():
#             time.sleep(60)
#     except KeyboardInterrupt:
#         print "\nQUITTING\n"
#         logging.warn("Ctrl-C")
#         while controller.running():
#             controller.stop()
#             time.sleep(0.1)
#
#
# if __name__ == "__main__":
#     main()


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
