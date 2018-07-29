#!/usr/bin/python

import hcsr04sensor.sensor as sensor

import debug
import time

import tank
import logging
import logg
import cfg

class DistSensor(tank.Ticker):
    def __init__(self, config):
        super(DistSensor, self).__init__()
        self.config = config
        self._current_dist = 100.0
        self._logger = logg.TankLog()
        self._action_interval = 20
        self._next_read_time = 0  # self.time_next_action()
        if debug.TEMP_TEST != 0:
            self._current_dist = self.test_dist()

    def test_dist(self):
        """
        Provides Test Values
        """
        if self.config.name.startswith('tank'):
            return 21.5
        else:
            return 24.5

    @property
    def current_value(self):
        return self._current_dist

    def get_new_relay_state(self, onval=None, offval=None):
        """
        Return the state the controlled object should be in according to passed in values
        """
        if onval is None or offval is None:
            return 0

        if onval >= offval:
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
#        self._logger.log_value(self.config.name, "{dist}".format(dist=int(self._current_dist)))
#        return
#        if 'OFF' in self.config.control_state and self.config.always_active == 0 and self._current_dist != 0:
#            pass
#        else:
         now = time.time()
         if now >= self._next_read_time:
             self._get_distance()
             self._next_read_time = self.time_next_action()
             logging.info("{s} dist {t}".format(s=self.config.name, t=self._current_dist))
             self._logger.log_value(self.config.name, "{dist}".format(dist=int(self._current_dist)))

    def _get_distance(self):
        if debug.DIST_TEST != 0:
            self._current_dist = self.test_dist()
        else:
            round_to = 1
            temperature = 20  # TODO
            self._error_count = 0
            value = sensor.Measurement(self.config.trig_pin, self.config.echo_pin, temperature, 'metric', round_to)
            raw_distance = value.raw_distance()

            # If tank depth is defined then give a water depth
            if self.config.tank_depth is not None:
                water_depth = value.depth_metric(raw_distance, self.config.tank_depth)
                if water_depth < 0:
                    water_depth = 0.0
                self._current_dist = water_depth
            else:
                # otherwise give a distance to water surface
                self._current_dist = raw_distance
            # logging.info("{x}".format(x=self._current_dist))


def main():
  config = cfg.Config()


  dist_cfg = config.get_items(cfg.DIST_TYPE)[0]
  ds = DistSensor(dist_cfg)

  while True:
    ds._get_distance()
    print ds.current_value
    time.sleep(1)




if __name__ == '__main__':
    main()

