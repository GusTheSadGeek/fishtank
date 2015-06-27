#!/usr/bin/python
import datetime
import threading
import time
import relayController

# class Relay:
#     def __init__(self, new_id):
#         self.id = new_id
#
#     def state(self, new_state):
#         print "{id} {state}".format(id=self.id, state=new_state)


class SchdEntry:
    def __init__(self, s):
        f = s.split(' ')
        self.day = f[0]
        self.function = f[2]
        hm = f[1].split(':')
        self.time = datetime.time(int(hm[0]), int(hm[1]), 0, 0)
        self.secs = (int(hm[0]) * 3600) + (int(hm[1]) * 60)

    def this_day(self, day):
        days = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
        d = days[day]

        if 'all' in self.day:
            return True

        if d in self.day:
            return True

        if (day < 5) and ('wkd' in self.day):
            return True

        if (day > 4) and ('wke' in self.day):
            return True

        return False


class Schedule:

    def __init__(self):
        self.s = list()

    def set(self, entry):
        self.s.append(entry)

    def current_state(self, day, seconds):
        state = '?'
        for q in self.s:
            if q.this_day(day):
                if q.secs < seconds:
                    state = q.function
        return state


class Timer:
    def __init__(self, schedule, relay):
        self.schedule = schedule
#        self.schedule = Schedule()
        self.relay = relay
        self.current_state = '?'
        self.thread = threading.Thread(target=self.timer_thread)
        self._stop = False

    def tick(self, now=None):
        if now is None:
            now = datetime.datetime.today()
        day_of_week = now.weekday()
        seconds_since_midnight = (now - now.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()

        state = self.schedule.current_state(day_of_week, seconds_since_midnight)

        if state != self.current_state:
            print 'Setting Relay to {s}'.format(s=state)
            self.current_state = state
        self.relay.set_state(state)

    def start(self):
        self.thread.start()

    def stop(self):
        self._stop = True

    def timer_thread(self):
        while not self._stop:
            self.tick()

            q = 0
            while q < 60 and not self._stop:
                time.sleep(1)
                q += 1

        print "stopping_1"



#while True:
#    time.sleep(100)

# t.tick(datetime.datetime(year=1, month=1, day=6, hour=0, minute=1))
# t.tick(datetime.datetime(year=1, month=1, day=6, hour=1, minute=0))
# t.tick(datetime.datetime(year=1, month=1, day=6, hour=2, minute=0))
# t.tick(datetime.datetime(year=1, month=1, day=6, hour=3, minute=0))
# t.tick(datetime.datetime(year=1, month=1, day=6, hour=4, minute=0))
# t.tick(datetime.datetime(year=1, month=1, day=6, hour=5, minute=0))
# t.tick(datetime.datetime(year=1, month=1, day=6, hour=6, minute=0))
# t.tick(datetime.datetime(year=1, month=1, day=6, hour=7, minute=0))
# t.tick(datetime.datetime(year=1, month=1, day=6, hour=8, minute=0))
# t.tick(datetime.datetime(year=1, month=1, day=6, hour=9, minute=0))
# t.tick(datetime.datetime(year=1, month=1, day=6, hour=10, minute=0))
# t.tick(datetime.datetime(year=1, month=1, day=6, hour=11, minute=0))
# t.tick(datetime.datetime(year=1, month=1, day=6, hour=12, minute=0))
# t.tick(datetime.datetime(year=1, month=1, day=6, hour=13, minute=0))
# t.tick(datetime.datetime(year=1, month=1, day=6, hour=14, minute=0))
# t.tick(datetime.datetime(year=1, month=1, day=6, hour=15, minute=0))
# t.tick(datetime.datetime(year=1, month=1, day=6, hour=16, minute=0))
# t.tick(datetime.datetime(year=1, month=1, day=6, hour=17, minute=0))
# t.tick(datetime.datetime(year=1, month=1, day=6, hour=18, minute=0))
# t.tick(datetime.datetime(year=1, month=1, day=6, hour=19, minute=0))
# t.tick(datetime.datetime(year=1, month=1, day=6, hour=20, minute=0))
# t.tick(datetime.datetime(year=1, month=1, day=6, hour=21, minute=0))
# t.tick(datetime.datetime(year=1, month=1, day=6, hour=22, minute=0))
# t.tick(datetime.datetime(year=1, month=1, day=6, hour=23, minute=1))
