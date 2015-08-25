#!/usr/bin/python

import tank_debug
import time
import datetime

import tank
import logging
import tank_log


class TempSensor(tank.Ticker):
    def __init__(self, cfg):
        super(TempSensor, self).__init__()
        self._sensor_file = cfg['sensor']
        self._current_temp = 0
        self._name = cfg['name']
        self._next_read_time = time.time()
        self._logger = tank_log.TankLog()
        self._action_interval = 60
        if tank_debug.TEMP_TEST != 0:
            self._current_temp = self.test_temp()

    def test_temp(self, m=None):
        """
        Provides Test Values
        """
        if m is None:
            now = datetime.datetime.now()
            m = now.minute
        m1 = m % 15
        if (m % 30) > 14:
            m1 *= -1
            m1 += 15
        d = m1 * 0.1
        if self._name.startswith('tank'):
            return 21.5 + d
        else:
            return 24.5 + d

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
        now = time.time()
        if now >= self._next_read_time:
            self._read_temp()
            self._next_read_time = self.time_next_action()
            logging.info("{s} temp {t}".format(s=self.name, t=self._current_temp))
            self._logger.log_value(self.name, "{temp:6.3f}".format(temp=self._current_temp))

    def _get_temp_raw(self):
        if tank_debug.TEMP_TEST == 0:
            try:
                with open(self._sensor_file, 'r') as f:
                    lines = f.readlines()
            except IOError:
                lines = None
                logging.error("Failed to read sensor {f}".format(f=self._sensor_file))
                pass
        else:
            lines = [
                "76 01 55 00 7f ff 0c 10 ee : crc=ee YES",
                "76 01 55 00 7f ff 0c 10 ee t=23375"
            ]
        return lines

    def _read_temp(self):
        if tank_debug.TEMP_TEST != 0:
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


def main():
    pass

if __name__ == "__main__":
    #    log,a,b = get_temp_log(5)
    #    print log
    #    print a,b
    main()
