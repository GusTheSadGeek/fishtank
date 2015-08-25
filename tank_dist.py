#!/usr/bin/python

import hcsr04sensor.sensor as sensor

import tank_debug
import time
import datetime

import tank
import tank_cfg
import logging
import tank_log

# configs = {'critical_water_level': config.getint('pit', 'critical_water_level'),
#            'pit_depth': config.getint('pit', 'pit_depth'),
#            'temperature': config.getint('pit', 'temperature'),
#            'trig_pin': config.getint('gpio_pins', 'trig_pin'),
#            'echo_pin': config.getint('gpio_pins', 'echo_pin'),
#            'unit': config.get('pit', 'unit')
#            }


class DistSensor(tank.Ticker):
    def __init__(self, cfg):
        super(DistSensor, self).__init__()
        self.trig_pin = cfg[tank_cfg.ITEM_TRIGPIN]
        self.echo_pin = cfg[tank_cfg.ITEM_ECHOPIN]
        self.tank_depth = cfg[tank_cfg.ITEM_TANKDEPTH]
        self._current_dist = 0
        self._name = cfg['name']
        self._next_read_time = time.time()
        self._logger = tank_log.TankLog()
        self._action_interval = 60
        if tank_debug.TEMP_TEST != 0:
            self._current_dist = self.test_dist()

    def test_dist(self, m=None):
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
        d = m1
        if self._name.startswith('tank'):
            return 21.5 + d
        else:
            return 24.5 + d

    @property
    def current_value(self):
        return self._current_dist

    def get_new_relay_state(self, onval=None, offval=None):
        """
        Return the state the controlled object should be in according to passed in values
        """
        if onval is None or offval is None:
            return 0

        if onval > offval:
            if self._current_dist >= onval:
                return 1
            if self._current_dist < offval:
                return -1
        else:
            if self._current_dist <= onval:
                return 1
            if self._current_dist > offval:
                return -1
        return 0

    # Override base
    def tick(self):
        now = time.time()
        if now >= self._next_read_time:
            self._get_distance()
            self._next_read_time = self.time_next_action()
            logging.info("{s} temp {t}".format(s=self.name, t=self._current_dist))
            self._logger.log_value(self.name, "{dist:6.1f}".format(dist=self._current_dist))

    def _get_distance(self):
        if tank_debug.DIST_TEST != 0:
            self._current_dist = self.test_dist()
        else:
            round_to = 1
            temperature = 20  # TODO

            value = sensor.Measurement(self.trig_pin, self.echo_pin, temperature, 'metric', round_to)
            raw_distance = value.raw_distance()

            # If tank depth is defined then give a water depth
            if self.tank_depth is not None:
                water_depth = value.depth_metric(raw_distance, self.tank_depth)
                self._current_dist = water_depth
            else:
                # otherwise give a distance to water surface
                self._current_dist = raw_distance


def main():
    pass

if __name__ == "__main__":
    main()


#
#
#
#
#
#
#
#
# #import raspisump.log as log
# #import raspisump.alerts as alerts
#
# config = ConfigParser.RawConfigParser()
# config.read('/home/pi/raspi-sump/raspisump.conf')
#
# configs = {'critical_water_level': config.getint('pit', 'critical_water_level'),
#            'pit_depth': config.getint('pit', 'pit_depth'),
#            'temperature': config.getint('pit', 'temperature'),
#            'trig_pin': config.getint('gpio_pins', 'trig_pin'),
#            'echo_pin': config.getint('gpio_pins', 'echo_pin'),
#            'unit': config.get('pit', 'unit')
#            }
#
# # If item in raspisump.conf add to configs dict above
# try:
#     configs['alert_when'] = config.get('pit', 'alert_when')
#
# # if not in raspisump.conf , provide a default value
# except ConfigParser.NoOptionError:
#     configs['alert_when'] = 'high'
#
#
# def water_reading():
#     '''Initiate a water level reading.'''
#     pit_depth = configs['pit_depth']
#     critical_water_level = configs['critical_water_level']
#     trig_pin = configs['trig_pin']
#     echo_pin = configs['echo_pin']
#     round_to = 1
#     temperature = configs['temperature']
#     unit = configs['unit']
#
#     value = sensor.Measurement(trig_pin, echo_pin, temperature, unit, round_to)
#     raw_distance = value.raw_distance()
#
#     if unit == 'imperial':
#         water_depth = value.depth_imperial(raw_distance, pit_depth)
#     if unit == 'metric':
#         water_depth = value.depth_metric(raw_distance, pit_depth)
#
#     generate_log(water_depth)
#     generate_alert(water_depth, critical_water_level)
#
#
# def generate_log(water_depth):
#     '''Log water level reading to a file.'''
#     log.log_reading(water_depth)
#
#
# def generate_alert(water_depth, critical_water_level):
#     '''Determine if an alert is required and initiate one if it is.'''
#     if water_depth > critical_water_level and configs['alert_when'] == 'high':
#         alerts.determine_if_alert(water_depth)
#     elif water_depth < critical_water_level and configs['alert_when'] == 'low':
#         alerts.determine_if_alert(water_depth)
#     else:
#         pass
