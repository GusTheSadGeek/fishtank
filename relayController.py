#!/usr/bin/python
import RPi.GPIO as GPIO

import timer

class Controller():
    def __init__(self):
        self.relays = Relays()
        self.relay0 = self.relays.get_relay(0)
        self.relay1 = self.relays.get_relay(1)

        s1 = timer.Schedule()
        s1.set(timer.SchdEntry("wkd 00:00 off"))
        s1.set(timer.SchdEntry("wkd 14:30 on"))
        s1.set(timer.SchdEntry("wkd 22:30 off"))

        s1.set(timer.SchdEntry("wke 00:00 off"))
        s1.set(timer.SchdEntry("wke 12:30 on"))
        s1.set(timer.SchdEntry("wke 22:30 off"))

        s2 = timer.Schedule()
        s2.set(timer.SchdEntry("wkd 00:00 off"))
        s2.set(timer.SchdEntry("wkd 15:00 on"))
        s2.set(timer.SchdEntry("wkd 23:00 off"))

        s2.set(timer.SchdEntry("wke 00:00 off"))
        s2.set(timer.SchdEntry("wke 13:00 on"))
        s2.set(timer.SchdEntry("wke 23:00 off"))

        self.schedule1 = s1
        self.schedule2 = s2

        self.t1 = None
        self.t2 = None

        self.states = ['OFF', 'ON']


    def init_timers(self):
        self.t1 = timer.Timer(self.schedule1, self.relay0)
        self.t1.start()

        self.t2 = timer.Timer(self.schedule2, self.relay1)
        self.t2.start()

    def get_relay_state(self, n):
        return self.relays.get_relay(n).state()

    def get_relay_state_str(self, n):
        a, t, o = self.relays.get_relay(n).state()

        actual = self.states[a]
        timer = self.states[t]
        override = self.states[o]
        return "Actual:"+actual+"   Timer:"+timer+"   Override:"+override

    def toggle(self, n):
        r = self.relays.get_relay(n)
        actual_state, tstate, ostate = r.state()
        if actual_state == 1:
            r.turn_relay_off()
        else:
            r.turn_relay_on()


    def stop(self):
        self.t1.stop()
        self.t2.stop()
        self.relays.cleanup()

class Relays():
    def __init__(self):
#        self.pinList = [18, 22, 24, 26]
        self.pinList = [11, 13, 15, 16]
        GPIO.setmode(GPIO.BOARD)

        self.relays = []

        self.relays.append(Relay(0, self.pinList[0]))
        self.relays.append(Relay(1, self.pinList[1]))
        self.relays.append(Relay(2, self.pinList[2]))
        self.relays.append(Relay(3, self.pinList[3]))

    def get_relay(self, n):
        return self.relays[n]

    def cleanup(self):
        GPIO.cleanup()


class Relay:
    def __init__(self, new_id, pin):
        self.id = new_id
        self.pin = pin
        self.current_state = 0
        self.timer_state = 0
        GPIO.setup(self.pin, GPIO.OUT)
        self.turn_relay_off()
        self.override = 0

    def turn_relay_on(self):
        print self.id, "ON"
        GPIO.output(self.pin, GPIO.LOW)
        self.current_state = 1

    def turn_relay_off(self):
        print self.id, "OFF"
        GPIO.output(self.pin, GPIO.HIGH)
        self.current_state = 0

    def set_state(self, new_state):
        print "{id} {state}".format(id=self.id, state=new_state)
        if "on" in new_state:
            self.timer_state = 1
            if not self.override:
                self.turn_relay_on()
        else:
            self.timer_state = 0
            if not self.override:
                self.turn_relay_off()

    def toggle_override(self):
        if self.override == 0:
            self.override = 1
        else:
            self.override = 0

    def state(self):
        return self.current_state, self.timer_state, self.override


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
