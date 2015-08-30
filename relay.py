#!/usr/bin/python

import debug
import logging
import cfg
import logg
import tank


if debug.RELAY_TEST == 0:
    import RPi.GPIO as GPIO
else:
    import DUMMY_GPIO as GPIO
    print "DEBUG RELAY"

# states = ['OFF', 'ON']
#
# class RelayState:
#     OFF = 0
#     ON = 1
#     FOFF = 2
#     FON = 3
#     UNKNOWN = 4
#
#     @classmethod
#     def to_string(cls, n):
#         if n == cls.OFF:
#             return 'OFF'
#         if n == cls.ON:
#             return 'ON'
#         if n == cls.FOFF:
#             return 'FORCED OFF'
#         if n == cls.FON:
#             return 'FORCED ON'
#         return 'UNKNOWN'


class Relay(tank.Ticker):
    OFF = 0
    ON = 1
    FOFF = 2
    FON = 3
    UNKNOWN = 4

    def __init__(self, config):
        super(Relay, self).__init__()
        self._name = config[cfg.ITEM_NAME]
        self.pin = config[cfg.ITEM_PIN]
        self.controlledby = config[cfg.ITEM_CONTROLLEDBY]
        self.controlledby_and = config[cfg.ITEM_CONTROLLEDBY_AND]
        self.controlledby_or = config[cfg.ITEM_CONTROLLEDBY_OR]
        self.controller = None
        self.controller_or = None
        self.controller_and = None
        self._logger = logg.TankLog()
        self.on_temp = config[cfg.ITEM_ONVAL]
        self.off_temp = config[cfg.ITEM_OFFVAL]
        self.on_temp2 = config[cfg.ITEM_ONVAL2]
        self.off_temp2 = config[cfg.ITEM_OFFVAL2]
        self.avg = []
        self.moving_total = 0.0
        self.controller_state = 99
        self.current_state = Relay.UNKNOWN

    def init(self):
        if self.controlledby is not None:
            self.controller = cfg.Config().get_item(self.controlledby)
        if self.controlledby_and is not None:
            self.controller_and = cfg.Config().get_item(self.controlledby_and)
        if self.controlledby_or is not None:
            self.controller_or = cfg.Config().get_item(self.controlledby_or)
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.pin, GPIO.OUT)
        self.turn_relay_off()

    def tick(self):
        if self.controller is not None:
            if 'OFF' in tank.general_control():
                new_state = -1
            else:
                new_state = self.controller.get_new_relay_state(self.on_temp, self.off_temp)
                # print "{name} {n}".format(name=self._name, n=new_state)

                if self.controller_and is not None:
                    new_statea = self.controller_and.get_new_relay_state(self.on_temp2, self.off_temp2)
                    # print "AND {name} {n}".format(name=self._name, n=new_statea)
                    q = -1
                    if (new_state == 1) and (new_statea == 1):
                        q = 1
                    if (new_state == -1) and (new_statea == -1):
                        q = -1
                    new_state = q

                else:
                    if self.controller_or is not None:
                        new_stateo = self.controller_or.get_new_relay_state(self.on_temp2, self.off_temp2)
                        # print "OR {name} {n}".format(name=self._name, n=new_stateo)
                        q = 0
                        if (new_state == 1) and (new_stateo == 1):
                            q = 1
                        if (new_state == -1) and (new_stateo == -1):
                            q = -1
                        new_state = q

#            print "{name} {n}".format(name=self._name, n=new_state)

            if new_state == 1:
                self.set_state(True)
            if new_state == -1:
                self.set_state(False)
        if self.current_state == Relay.ON or self.current_state == Relay.FON:
            new_val = 5
        else:
            new_val = 0
        self.avg.append(new_val)
        if len(self.avg) > 720:
            old_val = self.avg.pop(0)
            self.moving_total -= old_val
        self.moving_total += new_val

        avg = (self.moving_total / (len(self.avg)*5)) * 100

        self._logger.log_value(self._name,
                               "{avg:4.1f}".format(avg=avg),
                               "{current}".format(current=self.state_to_string(self.current_state)))

    def turn_relay_on(self):
        if self.current_state != Relay.ON:
            logging.info(str(self.name)+" ON")
        GPIO.output(self.pin, GPIO.LOW)
        self.current_state = Relay.ON

    def turn_relay_off(self):
        if self.current_state != Relay.OFF:
            logging.info(str(self._name)+" OFF")
            GPIO.output(self.pin, GPIO.HIGH)
        self.current_state = Relay.OFF

    def force_relay_on(self):
        if self.current_state != Relay.FON:
            logging.info(str(self._name)+" FON")
        GPIO.output(self.pin, GPIO.LOW)
        if self.controller_state == 1:
            self.current_state = Relay.ON
            logging.info(str(self._name)+" ON")
        else:
            self.current_state = Relay.FON

    def force_relay_off(self):
        if self.current_state != Relay.FOFF:
            logging.info(str(self._name)+" FOFF")
        GPIO.output(self.pin, GPIO.HIGH)
        if self.controller_state == 0:
            self.current_state = Relay.OFF
            logging.info(str(self._name)+" OFF")
        else:
            self.current_state = Relay.FOFF

    # def unforce_relay(self):
    #     if self.current_state == RelayState.FOFF:
    #         logging.info(str(self._name)+" OFF")
    #         GPIO.output(self.pin, GPIO.LOW)
    #         self.current_state = RelayState.OFF
    #     if self.current_state == RelayState.FON:
    #         logging.info(str(self._name)+" ON")
    #         GPIO.output(self.pin, GPIO.HIGH)
    #         self.current_state = RelayState.ON

    def set_state(self, new_state):
        # print "{name} {state}".format(name=self._name, state=new_state)
        if new_state != self.controller_state:
            if new_state:
                self.controller_state = 1
                self.turn_relay_on()
            else:
                self.controller_state = 0
                self.turn_relay_off()
        if new_state:
            if self.current_state == Relay.FON:
                self.current_state = Relay.ON
        else:
            if self.current_state == Relay.FOFF:
                self.current_state = Relay.OFF

    def state(self):
        return self.current_state, self.controller_state

    def toggle(self):
        if self.current_state == Relay.ON or self.current_state == Relay.FON:
            self.force_relay_off()
        else:
            self.force_relay_on()
        self.tick()

    @classmethod
    def state_to_string(cls, n):
        if n == cls.OFF:
            return 'OFF'
        if n == cls.ON:
            return 'ON'
        if n == cls.FOFF:
            return 'FORCED OFF'
        if n == cls.FON:
            return 'FORCED ON'
        return 'UNKNOWN'
