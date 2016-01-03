"""
Module for measuring distance or depth with an HCSRO4 Ultrasonic sound
sensor and a Raspberry Pi.  Imperial and Metric measurements are available
"""

# Al Audet
# MIT License

import debug
import time
import math
import logging
import threading

if debug.DIST_TEST == 0:
    import RPi.GPIO as GPIO
else:
    import DUMMY_GPIO as GPIO
    print "DEBUG DIST"


class Measurement(object):
    """
    Create a measurement using a HC-SR04 Ultrasonic Sensor connected to
    the GPIO pins of a Raspberry Pi.
    """
    def __init__(self, trig_pin, echo_pin, temperature, unit, round_to):
        self.trig_pin = trig_pin
        self.echo_pin = echo_pin
        self.temperature = temperature
        self.unit = unit
        self.round_to = round_to
        self.sonar_signal_off = 0     # default value - for testing
        self.sonar_signal_on = 0.001  # default value - for testing
        self.myevent = threading.Event()
        # print self.echo_pin
        # print self.trig_pin
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BOARD)
        GPIO.remove_event_detect(self.echo_pin)
        GPIO.setup(self.trig_pin, GPIO.OUT)
        GPIO.setup(self.echo_pin, GPIO.IN)
        GPIO.add_event_detect(self.echo_pin, GPIO.BOTH)
        GPIO.add_event_callback(self.echo_pin, self.sig_callback)

    def tidy_up(self):
        """
        Never actually called (at the moment) !
        :return:
        """
        # Only cleanup the pins used to prevent clobbering any others in use by the program
        GPIO.cleanup(self.trig_pin)
        GPIO.cleanup(self.echo_pin)
        GPIO.remove_event_detect(self.echo_pin)

    def raw_distance(self):
        """
        :return:an error corrected unrounded distance, in cm, of an object
        adjusted for temperature in Celcius.  The distance calculated
        is the median value of a sample of 11 readi
        """
        if self.unit == 'imperial':
            self.temperature = (self.temperature - 32) * 0.5556
        elif self.unit == 'metric':
            pass
        else:
            raise ValueError(
                'Wrong Unit Type. Unit Must be imperial or metric')

        speed_of_sound = 331.3 * math.sqrt(1+(self.temperature / 273.15))
        sample = []
        for distance_reading in range(11):

            GPIO.output(self.trig_pin, GPIO.LOW)
            time.sleep(1.0)
            GPIO.output(self.trig_pin, GPIO.HIGH)
            time.sleep(0.001)
            GPIO.output(self.trig_pin, GPIO.LOW)

            self.myevent.clear()
            self.sonar_signal_off = None
            self.sonar_signal_on = None

            if self.myevent.wait(2):  # Wait MAX of 2 seconds for returned pulse
                if self.sonar_signal_on is not None and self.sonar_signal_off is not None:
                    time_passed = self.sonar_signal_on - self.sonar_signal_off
                    distance_cm = time_passed * ((speed_of_sound * 100) / 2)
                    sample.append(distance_cm)
            else:
                logging.warning("Distance sensor took too long")
        sorted_sample = sorted(sample)
        # print sorted_sample
        total = 0.0
        for d in sorted_sample[1:-1]:
            total += d
        mean = total/(len(sorted_sample)-2)
        logging.debug("median = {med}   mean = {mean}".format(med=sorted_sample[5], mean=mean))
        return sorted_sample[5]

    def sig_callback(self, pin):
        t = time.time()
        if pin == self.echo_pin:
            if self.sonar_signal_off is None:
                self.sonar_signal_off = t
            else:
                self.sonar_signal_on = t
                self.myevent.set()

    def depth_metric(self, median_reading, hole_depth):
        """
        Calculate the rounded metric depth of a liquid. hole_depth is the
        distance, in cm's, from the sensor to the bottom of the hole.
        :param median_reading:
        :param hole_depth:
        :return: dpeth in cm's
        """
        return round(hole_depth - median_reading, self.round_to)

    def depth_imperial(self, median_reading, hole_depth):
        """
        Calculate the rounded imperial depth of a liquid. hole_depth is the
        distance, in inches, from the sensor to the bottom of the hole.
        :param median_reading:
        :param hole_depth:
        :return: depth in inches
        """
        return round(hole_depth - (median_reading * 0.394), self.round_to)

    def distance_metric(self, median_reading):
        """
        Calculate the rounded metric distance, in cm's, from the sensor
        to an object
        :param median_reading:
        :return: distance, in cm's
        """
        return round(median_reading, self.round_to)

    def distance_imperial(self, median_reading):
        """
        Calculate the rounded imperial distance, in inches, from the sensor
        to an oject.
        :param median_reading:
        :return: distan in inches
        """
        return round(median_reading * 0.394, self.round_to)
