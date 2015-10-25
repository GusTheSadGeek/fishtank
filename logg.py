#!/usr/bin/python

import os
import time
import datetime
import copy

import logging
import cfg
import tank


value_log_file = '/var/log/tank/temps.txt'
current_value_file = '/mnt/ram/current_temps.txt'

seconds_in_day = (3600 * 24)


class LogLine(object):
    def __init__(self, line):
        self.OK = False
        try:
            if type(line) is int:
                self.fields = ['TS']
                self.ts = line
            else:
                self.fields = line.strip(',').split(',')
                self.ts = int(self.fields[0])
            self.OK = True
        except:
            self.OK = False

    def differ(self, a):
        if a is None:
            return True

        for i in range(1, len(a.fields)):
            if a.fields[i] != self.fields[i]:
                return True
        return False


def log_file_name(ts=None):
    if ts is None:
        now = datetime.datetime.now()
    else:
        now = datetime.datetime.fromtimestamp(ts)
    filename = "/var/log/tank/T{a}_{b}_{c}.txt".format(a=now.year, b=now.month, c=now.day)
    return filename


def find_next_log_file(ts):
    now = time.time()
    while ts < now:
        fname = log_file_name(ts)
        ts += (24 * 3600)
        if os.path.isfile(fname):
            return ts, fname
    return -1 , ""


def setup_log():
    default_log_dir = r'/var/log/tank/'
    default_logfile = default_log_dir+r'/temp.log'

    if not os.path.exists(default_log_dir):
        os.makedirs(default_log_dir)

    logging.basicConfig(filename=default_logfile, level=logging.DEBUG,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s')


def time_now_text():
    now = datetime.datetime.now()
    date = "{a},{b},{c},{d},{e}". \
        format(a=now.year, b=now.month-1, c=now.day, d=now.hour, e=now.minute)
    return date


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
            self.previous_log_values = {}
            self.current_values = {}
            self.cols = {}
            self.tna = self.time_next_action(cfg.Config().log_interval)

    def init(self):
        for item in cfg.Config().items:
            if item is not None:
                if item.logcol is not None:
                    if item.logcol is not None:
                        self.cols[item.logcol] = item.name

    def log_value(self, key, logvalue, current=None):
        if current is None:
            current = logvalue
        self.current_values[key] = str(current)
        self.current_log_values[key] = str(logvalue)

    def update_log_file(self):
        logging.info("logging")
        now = str(int(time.time()))
#        now = time_now_text()
        temps_output = []
        for col in range(10):
            if col in self.cols:
                temps_output.append("{val}".format(val=self.current_log_values[self.cols[col]]))

        # date = "{a},{b},{c},{d},{e}". \
        #     format(a=now.year, b=now.month-1, c=now.day, d=now.hour, e=now.minute)

        output2 = "{date:s},{temps:s}\n". \
            format(date=now, temps=','.join(temps_output))

        log_fname = log_file_name()
        try:
            with open(log_fname, 'a') as f:
                f.write(output2)
        except IOError as e:
            logging.error(str(e))
            logging.error("Error writing to temp file {f}".format(log_fname))

    def tick(self):
        try:
            with open(current_value_file, 'w') as f:
                s = "ControlState={temp}\n".format(temp=cfg.Config().control_state)
                f.write(s)
                for key, value in self.current_values.iteritems():
                    s = "{name}={temp}\n".format(name=key, temp=value)
                    f.write(s)
        except IOError as e:
            logging.error(str(e))
            logging.error("Error writing to temp file {f}".format(current_value_file))

        changed = False
        for key in self.current_log_values:
            if key in self.previous_log_values:
                if self.previous_log_values[key] != self.current_log_values[key]:
                    changed = True
                    break
            else:
                changed = True
                break
        if changed:
            self.update_log_file()
            for key in self.current_log_values:
                self.previous_log_values[key] = self.current_log_values[key]


prefetch_data = []

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

    @classmethod
    def convert_1(cls):
        out_file_name = ""
        in_file_name = value_log_file
        fp_out = None
        try:
            with open(in_file_name, 'r') as f:
                log = f.read().split('\n')
        except IOError:
            log = "error"

        for line1 in log:
            line = line1.strip(',')
            if len(line) > 5:
                fields = line.split(',')
            if fields[0] == '2015':
                n = map((lambda x: int(x)), fields[0:5])
                ts = int(datetime.datetime(n[0], n[1]+1, n[2], n[3], n[4]).strftime('%s'))
                coloffset = 5
            else:
                coloffset = 1
                ts = int(fields[0])
            new_line = "{ts},{data}\n".format(ts=ts, data=','.join(fields[coloffset:]))

            new_out_file_name = log_file_name(ts)

            if new_out_file_name != out_file_name:
                out_file_name = new_out_file_name
                if fp_out is not None:
                    fp_out.close()
                fp_out = open(out_file_name, 'w')
            if fp_out is not None:
                fp_out.write(new_line)

        if fp_out is not None:
            fp_out.close()


    def prefetch(self, days, span=9999):
        global prefetch_data
        prefetch_data = []

        now = int(time.time())
        start_ts = int(time.time()) - (days * seconds_in_day)
        end_ts = start_ts + (span * seconds_in_day)

        log = []
        ts2 = start_ts
        while ts2>0 and ts2 <= end_ts:
            ts2, file_name = find_next_log_file(ts2)
            try:
                with open(file_name, 'r') as f:
                    log2 = f.read().split('\n')
                    log.extend(log2)
            except IOError:
                log2 = "error"

        # config = cfg.Config()
        #
        # ret_lines = []
        # prev = None
        # prev_ts = 0
        index = 0
        log_len = len(log)
        # delta = None
        while index < log_len:
            # current = []
            line = LogLine(log[index])
            if line.OK:
                if line.ts > end_ts:
                    break

                if start_ts <= line.ts <= end_ts:
                    prefetch_data.append(line)
            index += 1
        return len(prefetch_data)


    def get_log(self, days, graph_type, span=9999):
        now = int(time.time())
        start_ts = int(time.time()) - (days * seconds_in_day)
        end_ts = start_ts + (span * seconds_in_day)

        # file_name = value_log_file
        # try:
        #     with open(file_name, 'r') as f:
        #         log = f.read().split('\n')
        # except IOError:
        #     log = "error"

        config = cfg.Config()
        # Which log cols do we want ?
        log_cols = []
        sensors = []
        for gi in config.graphed_items:
            if graph_type is None or gi.graph == graph_type:
                log_cols.append(gi.logcol)
                sensors.append(gi.name)

        ret_lines = []
        prev = None
        prev_ts = 0
        index = 0
        log_len = len(prefetch_data)
        delta = None
        while index < log_len:
            current = None
            line = prefetch_data[index]
            if line.OK:

                if line.ts > end_ts:
                    break

                if start_ts <= line.ts <= end_ts:
                    current = LogLine(line.ts)
                    for lc in log_cols:
                        if len(line.fields) > lc:
                            current.fields.append(line.fields[lc])
                            self.update_min_max_values(float(line.fields[lc]))
                        else:
                            current.fields.append("0")
                        #current.append(value)

                    if current.differ(prev):
                        if prev is not None:
                            if line.ts > (prev.ts + 301):
                                p = copy.copy(prev)
                                p.ts = line.ts-1-delta
                                ret_lines.append(p)
                    #
                        if delta is None:
                            delta = line.ts + 1
                        else:
                            current.ts -= delta+1

                        ret_lines.append(current)
                        prev = current

            index += 1
        # if prev is not None:
        #     retline = str(now)+','
        #     ret_lines.append(retline+','.join(prev))

        return ret_lines, sensors

    def get_log2(self, days, graph_type, span=9999):

        start_day = days - span

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
            if graph_type is None or gi.graph == graph_type:
                log_cols.append(gi.logcol)
                sensors.append(gi.name)

        ret_lines = []
        day_count = 0
        last_day = None
        prev = None
        for index in range(len(log)-1, -1, -1):
            try:
                current = []
                line = log[index].strip(',')
                if len(line) > 5:
                    fields = line.split(',')
                    day = fields[2]
                    if day != last_day:
                        if last_day is not None:
                            day_count += 1
                        last_day = day
                    if day_count >= start_day:
                        for lc in log_cols:
                            if len(fields) > lc+4:
                                value = fields[lc+4]
                            else:
                                value = "0"
                            self.update_min_max_values(float(value))
                            current.append(value)

                        if current != prev:
                            if prev is None:
                                prev = current
                                retline = time_now_text()+',0,'
                                ret_lines.append(retline+','.join(prev))
                            else:
                                retline = fields[:5]
                                retline.append('1')
                                retline.extend(prev)
                                ret_lines.append(','.join(retline))

                            retline = fields[:5]
                            retline.append('0')
                            retline.extend(current)
                            ret_lines.append(','.join(retline))
                            prev = current

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
    output = u" ".join(out)
    return output


def log_last_changed():
    gtl = GetLog()
    return gtl.last_changed()


def get_temp_log(days, graph_type, span):
    start_time = time.time()

    s = time.time()
    gtl = GetLog()

    log, sensor_names = gtl.get_log(days, graph_type, span)

    # sensor_names = []
    # temps = GetTempLog().get_current()
    # for name, __ in temps.iteritems():
    #     sensor_names.append(name)

    end_time = time.time()
    logging.info("get_temp_log - "+str(len(log))+" "+str(graph_type)+"  "+str(end_time - start_time))
    return log, int(gtl.min_temp), int(gtl.max_temp+0.95), sensor_names


def prefetch(days, span):
    start_time = time.time()
    gtl = GetLog()
    length = gtl.prefetch(days, span)
    end_time = time.time()
    logging.info("prefetch - "+str(end_time - start_time))
    return length


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


def main():
    return GetLog().convert_1()

if __name__ == '__main__':
    main()
