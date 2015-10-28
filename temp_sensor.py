#!/usr/bin/python

import debug
import time

import tank
import logging
import logg
import send_alert

class TempSensor(tank.Ticker):
    def __init__(self, config):
        super(TempSensor, self).__init__()
        self.config = config
        self._current_temp = 0
        self._next_read_time = time.time()
        self._logger = logg.TankLog()
        self._action_interval = 60
        self._last_log_temp = 0
        self._last_alert = time.time()
        if debug.TEMP_TEST != 0:
            self._current_temp = self.test_temp()

    def test_temp(self):
        """
        Provides Test Values
        """
        if self.config.name.startswith('tank'):
            return 20.5
        else:
            return 24.5

    @property
    def current_value(self):
        return self._current_temp

    def get_new_relay_state(self, onval=None, offval=None):
        """
        Return the state the controlled object should be in according to passed in values
        """
        if onval is None or offval is None:
            return 0

        if onval > offval:
            if self._current_temp >= onval:
                return 1
            if self._current_temp < offval:
                return -1
        else:
            if self._current_temp <= onval:
                return 1
            if self._current_temp > offval:
                return -1
        return 0

    # Override base
    def tick(self):
        if 'OFF' in self.config.control_state and self.config.always_active == 0 and self._current_temp != 0:
            pass
        else:
            now = time.time()
            if now >= self._next_read_time:
                self._read_temp()
                self._next_read_time = self.time_next_action()
                diff = abs(self._current_temp - self._last_log_temp)
                if diff > 0.126:
                    logging.info("{s} temp {t}".format(s=self.config.name, t=self._current_temp))
                    self._last_log_temp = self._current_temp
                    self._logger.log_value(self.config.name, "{temp:1.1f}".format(temp=self._current_temp))
                if (self._current_temp > self.config.alert_max) or (self._current_temp < self.config.alert_min):
                    now = time.time()
                    if now > (self._last_alert + 900):
                        logging.critical("TEMP OUT OF RANGE {t}".format(t=self._current_temp))
                        send_alert.temp_err(self.config.alert_min, self.config.alert_max, self._current_temp)
                        self._last_alert = now

    def _get_temp_raw(self):
        if debug.TEMP_TEST == 0:
            try:
                with open(self.config.sensor, 'r') as f:
                    lines = f.readlines()
            except IOError:
                lines = None
                logging.error("Failed to read sensor {f}".format(f=self.config.sensor_file))
                pass
        else:
            lines = [
                "76 01 55 00 7f ff 0c 10 ee : crc=ee YES",
                "76 01 55 00 7f ff 0c 10 ee t=23375"
            ]
        return lines

    def _read_temp(self):
        if debug.TEMP_TEST != 0:
            self._current_temp = self.test_temp()
            return self._current_temp
        else:
            lines = self._get_temp_raw()
            while lines is not None and lines[0].strip()[-3:] != 'YES':
                time.sleep(0.2)
                lines = self._get_temp_raw()

            temp_output = lines[1].find('t=')
            if temp_output != -1:
                temp_string = lines[1].strip()[temp_output+2:]
                self._current_temp = float(temp_string) / 1000.0
                return self._current_temp
