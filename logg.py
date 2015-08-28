#!/usr/bin/python

import os
import time
import datetime

import logging
import cfg
import tank


value_log_file = '/var/log/tank/temps.txt'
current_value_file = '/mnt/ram/current_temps.txt'


def setup_log():
    default_log_dir = r'/var/log/tank/'
    default_logfile = default_log_dir+r'/temp.log'

    if not os.path.exists(default_log_dir):
        os.makedirs(default_log_dir)

    logging.basicConfig(filename=default_logfile, level=logging.DEBUG,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s')


class TankLog(tank.Ticker):
    """
    Borg (singleton) class
    """
    __shared_state = {}

    def __init__(self):
        self.__dict__ = self.__shared_state
        if '_first_time' not in self.__dict__:
            super(TankLog, self).__init__()
            self._first_time = False
            self.lines = ''
            self.current_log_values = {}
            self.current_values = {}
            self.interval = 120
            self.cols = {}
            self.tna = self.time_next_action()
#            self.tna = time.time()+10

    def init(self):
        for item in cfg.Config().items:
            if item is not None:
                if cfg.ITEM_LOGCOL in item:
                    if item[cfg.ITEM_LOGCOL] is not None:
                        self.cols[item[cfg.ITEM_LOGCOL]] = item[cfg.ITEM_NAME]

    def log_value(self, key, logvalue, current=None):
        if current is None:
            current = logvalue
        self.current_values[key] = str(current)
        self.current_log_values[key] = str(logvalue)

    def tick(self):
        try:
            with open(current_value_file, 'w') as f:
                for key, value in self.current_values.iteritems():
                    s = "{name}={temp}\n".format(name=key, temp=value)
                    f.write(s)
        except IOError as e:
            logging.error(str(e))
            logging.error("Error writing to temp file {f}".format(current_value_file))

#        now = time.time()
#        diff = self.tna - now
#        logging.debug("{n} {tnr} {diff}".format(n=now,tnr=self.tna,diff=diff))
        if self.tna < time.time():
            logging.info("logging")
            now = datetime.datetime.now()
            temps_output = []
            for col in range(10):
                if str(col) in self.cols:
                    temps_output.append("{val}".format(val=self.current_log_values[self.cols[str(col)]]))

            date = "{a},{b},{c},{d},{e}". \
                format(a=now.year, b=now.month-1, c=now.day, d=now.hour, e=now.minute)

            output2 = "{date:s},{temps:s}\n". \
                format(date=date, temps=','.join(temps_output))

            try:
                with open(value_log_file, 'a') as f:
                    f.write(output2)
            except IOError as e:
                logging.error(str(e))
                logging.error("Error writing to temp file {f}".format(value_log_file))

            self.tna = self.time_next_action()

    # def time_next_recording(self):
    #     now = datetime.datetime.now()
    #     secs_since_hour = (now.minute * 60) + now.second
    #     i = 0
    #     while i < secs_since_hour:
    #         i += self.interval
    #     r = time.time() + i - secs_since_hour
    #     return r

    # def get_temp(self, index):
    #     if len(self.sensors) < index:
    #         return self.sensors[index].current_temp
    #     else:
    #         return -1.0

    # def read_temp(self, index):
    #     if len(self.sensors) < index:
    #         return self.sensors[index].read_temp()
    #     else:
    #         return -1.0

    # def get_all(self):
    #     temps = []
    #     for s in self.sensors:
    #         temps.append(s.get_temp())
    #     return temps

    # def read_all(self):
    #     temps = []
    #     for s in self.sensors:
    #         temps.append(s.read_temp())
    #     return temps


class GetLog(object):
    def __init__(self):
        self.min_temp = 999.00
        self.max_temp = -999.00

    def update_min_max_values(self, temp):
        if temp > self.max_temp:
            self.max_temp = temp
        if temp < self.min_temp:
            self.min_temp = temp

    @classmethod
    def get_current(cls):
        temps = {}
        try:
            with open(current_value_file, 'r') as f:
                log = f.read()
            lines = log.split('\n')
            for l in lines:
                if len(l) > 3:
                    if '=' in l:
                        f = l.split('=')
                        temps[f[0]] = f[1]
        except IOError:
            logging.error("IOError: Could not get current temp from {f}".format(f=current_value_file))
        except IndexError:
            logging.error("IndexError: Could not get current temp from {f}".format(f=current_value_file))
        return temps

    @classmethod
    def last_changed(cls):
        # q = os.path.getmtime(value_log_file)
        return os.path.getmtime(value_log_file)

    def get_log(self, days, graph_type):
        # if mydebug.TEMP_TEST == 0:
        file_name = value_log_file
        # else:
        #    file_name = test_temp_file

        try:
            with open(file_name, 'r') as f:
                log = f.read().split('\n')
        except IOError:
            log = "error"

        config = cfg.Config()
        # Which log cols do we want ?
        log_cols = []
        sensors = []
        for gi in config.graphed_items:
            if graph_type is None or gi[cfg.ITEM_GRAPH] == graph_type:
                log_cols.append(int(gi[cfg.ITEM_LOGCOL]))
                sensors.append(gi[cfg.ITEM_NAME])

        ret_lines = []
        day_count = 0
        last_day = None
        for index in range(len(log)-1, -1, -1):
            try:
                line = log[index].strip(',')
                if len(line) > 5:
                    fields = line.split(',')
                    retline = fields[:5]
                    day = fields[2]
                    if day != last_day:
                        if last_day is not None:
                            day_count += 1
                        last_day = day
                    for lc in log_cols:
                        if len(fields) > lc+4:
                            value = fields[lc+4]
                        else:
                            value = "0.0"
                        self.update_min_max_values(float(value))
                        retline.append(value)
                    ret_lines.append(','.join(retline))
            except IndexError:
                logging.error("Index error in log file {line}".format(line=log[index]))
            except ValueError:
                logging.error("Value error in log file {line}".format(line=log[index]))

            if day_count >= days:
                break

                #        ret_lines = log[(index+1):]

        return ret_lines, sensors


def get_current_temps():
    """
    :return: All temps as strings
    """
    return GetLog().get_current()


def get_current_temp(field):
    """
    :param field: Name of temp required
    :return: requested temp as float
    """
    temps = get_current_temps()
    try:
        temp = float(temps[field])
    except KeyError:
        temp = 0.0
    return temp


def get_current_values_formatted():
    """
    :return: A formated string of all values
    """
    values = GetLog().get_current()
    out = []
    for name, value in values.iteritems():
        out.append(u"{name:s}:{temp:s}<br>".format(name=name, temp=value))
    output = u"    ".join(out)
    return output


def log_last_changed():
    gtl = GetLog()
    return gtl.last_changed()


def get_temp_log(days, graph_type):
    gtl = GetLog()

    log, sensor_names = gtl.get_log(days, graph_type)

    # sensor_names = []
    # temps = GetTempLog().get_current()
    # for name, __ in temps.iteritems():
    #     sensor_names.append(name)

    return log, int(gtl.min_temp), int(gtl.max_temp+0.95), sensor_names


def convert_log(infile, outfile):
    try:
        with open(infile, 'r') as f:
            log = f.readlines()
    except IOError:
        log = "error"

    with open(outfile, 'w') as f:
        for l in log:
            fields = l.split(',')
            a = ','.join(fields[1:4])
            newline = "2015,{a},0,{b},{c},\n".format(a=a, b=fields[5], c=fields[6][:-1])
            f.write(newline)
