#!/usr/bin/python
import datetime
import logging
import tank
import cfg


class Schedule:

    def __init__(self, file_name=None):
        self.s = []
        self.file = file_name
        if file_name is None:
            for __ in range(7):
                self.s.append(0)
        else:
            if self.load(file_name):
                self.s = []
                for __ in range(7):
                    self.s.append(0)
                self.save(file_name)

    def set(self, mon, tue, wed, thu, fri, sat, sun):
        self.s = []
        self.s.append(self._hex_string_to_int(mon))
        self.s.append(self._hex_string_to_int(tue))
        self.s.append(self._hex_string_to_int(wed))
        self.s.append(self._hex_string_to_int(thu))
        self.s.append(self._hex_string_to_int(fri))
        self.s.append(self._hex_string_to_int(sat))
        self.s.append(self._hex_string_to_int(sun))
        if self.file is not None:
            self.save(self.file)

    def load(self, file_name):
        self.file = file_name
        try:
            with open(file_name, 'r') as f:
                lines = f.read().split('\n')
            self.s = []
            for l in lines:
                if len(l) > 0:
                    self.s.append(self._hex_string_to_int(l))
        except IOError:
            return 1
        return 0

    def get_query(self):
        q = "mon=" + (hex(self.s[0])[2:]) +\
            "&" + "tue=" + hex(self.s[1])[2:] +\
            "&" + "wed="+hex(self.s[2])[2:] +\
            "&" + "thu="+hex(self.s[3])[2:] +\
            "&" + "fri="+hex(self.s[4])[2:] +\
            "&" + "sat="+hex(self.s[5])[2:] +\
            "&" + "sun="+hex(self.s[6])[2:]
        return q

    def save(self, file_name):
        with open(file_name, 'w') as f:
            for d in self.s:
                s = hex(d)[2:].replace('L', '')
                f.write(s + "\n")

    @staticmethod
    def _hex_string_to_int(h):
        return int(h.strip('L'), 16)

    def current_state(self, day, seconds):
        bit = 1 << int(seconds / 1800)
        return (self.s[day] & bit) > 0


class Timer(tank.Ticker):
    def __init__(self, config):
        super(Timer, self).__init__()
        self._name = config[cfg.ITEM_NAME]
        self._current_state = False
        filename = (self.name+'.sched').replace(' ', '_')
        self.schedule = Schedule(filename)

    def init(self):
        pass

    def new_schedule(self, mon, tue, wed, thu, fri, sat, sun):
        self.schedule.set(mon, tue, wed, thu, fri, sat, sun)

    def tick(self, now=None):
        if now is None:
            now = datetime.datetime.today()
        day_of_week = now.weekday()
        seconds_since_midnight = (now - now.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()

        state = self.schedule.current_state(day_of_week, seconds_since_midnight)

        if state != self._current_state:
            logging.info('{name} State changing to {s}'.format(name=self.name, s=state))
            self._current_state = state

    @property
    def state(self):
        return self._current_state

    def get_new_relay_state(self, onval=None, offval=None):
        if onval or offval:
            pass
        if self._current_state:
            return 1
        return -1


def get_query(file_name):
    s = Schedule(file_name)
    return s.get_query()


# while True:
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
