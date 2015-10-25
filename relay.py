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


class Relay(tank.Ticker):
    OFF = 0
    ON = 1
    FOFF = 2
    FON = 3
    UNKNOWN = 4

    def __init__(self, config):
        super(Relay, self).__init__()
        self.config = config
        self.controller = None
        self.controller_or = None
        self.controller_and = None
        self._logger = logg.TankLog()
        self.avg = []
        self.moving_total = 0.0
        self.controller_state = 99
        self.current_state = Relay.UNKNOWN

    def init(self):
        if self.config.controlledby is not None:
            self.controller = cfg.Config().get_item(self.config.controlledby)
        if self.config.controlledby_and is not None:
            self.controller_and = cfg.Config().get_item(self.config.controlledby_and)
        if self.config.controlledby_or is not None:
            self.controller_or = cfg.Config().get_item(self.config.controlledby_or)
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.config.pin, GPIO.OUT)
        self.turn_relay_off()

    def tick(self):
        if self.controller is not None:
            if 'OFF' in self.config.control_state and self.config.always_active == 0:
                new_state = -1
            else:
                new_state = self.controller.get_new_relay_state(self.config.onvalue, self.config.offvalue)
                # print "{name} {n}".format(name=self._name, n=new_state)

                if self.controller_and is not None:
                    new_statea = self.controller_and.get_new_relay_state(self.config.onvalue2, self.config.offvalue2)
                    # print "AND {name} {n}".format(name=self._name, n=new_statea)
                    q = -1
                    if (new_state == 1) and (new_statea == 1):
                        q = 1
                    if (new_state == -1) and (new_statea == -1):
                        q = -1
                    new_state = q

                else:
                    if self.controller_or is not None:
                        new_stateo = \
                            self.controller_or.get_new_relay_state(self.config.offvalue2, self.config.offvalue2)
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
            data_val = 1
        else:
            data_val = 0

        self._logger.log_value(self.config.name,
                               "{val}".format(val=data_val),
                               "{current}".format(current=self.state_to_string(self.current_state)))

    def turn_relay_on(self):
        if self.current_state != Relay.ON:
            logging.info(str(self.config.name)+" ON")
        GPIO.output(self.config.pin, GPIO.LOW)
        self.current_state = Relay.ON

    def turn_relay_off(self):
        if self.current_state != Relay.OFF:
            logging.info(str(self.config.name)+" OFF")
            GPIO.output(self.config.pin, GPIO.HIGH)
        self.current_state = Relay.OFF

    def force_relay_on(self):
        if self.current_state != Relay.FON:
            logging.info(str(self.config.name)+" FON")
        GPIO.output(self.config.pin, GPIO.LOW)
        if self.controller_state == 1:
            self.current_state = Relay.ON
            logging.info(str(self.config.name)+" ON")
        else:
            self.current_state = Relay.FON

    def force_relay_off(self):
        if self.current_state != Relay.FOFF:
            logging.info(str(self.config.name)+" FOFF")
        GPIO.output(self.config.pin, GPIO.HIGH)
        if self.controller_state == 0:
            self.current_state = Relay.OFF
            logging.info(str(self.config.name)+" OFF")
        else:
            self.current_state = Relay.FOFF

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
