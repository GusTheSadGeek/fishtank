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

        now = time.time()
        diff = self.tna - now
        logging.debug("{n} {tnr} {diff}".format(n=now,tnr=self.tna,diff=diff))
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
        q = os.path.getmtime(value_log_file)
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
            if gi[cfg.ITEM_GRAPH] == graph_type:
                log_cols.append(int(gi[cfg.ITEM_LOGCOL]))
                sensors.append(gi[cfg.ITEM_NAME])

        ret_lines = []
        index = 0
        day_count = 0
        last_day = None
        for index in range(len(log)-1, -1, -1):
            try:
                line = log[index].strip(',')
                if len(line) > 5:
                    fields = line.split(',')
                    retline = fields[:5]
                    values = fields[5:]
                    # for t in values:
                    #     self.update_min_max_values(float(t))
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




# class GetLog2(object):
#     def __init__(self):
#         self.min_value = 999.00
#         self.max_value = -999.00
#
#     def update_min_max_values(self, value):
#         if value > self.max_value:
#             self.max_value = value
#         if value < self.min_value:
#             self.min_value = value
#
#     @classmethod
#     def get_current(cls):
#         values = {}
#         try:
#             with open(current_value_file, 'r') as f:
#                 log = f.read()
#             lines = log.split('\n')
#             for l in lines:
#                 if len(l) > 3:
#                     if '=' in l:
#                         f = l.split('=')
#                         values[f[0]] = f[1]
#         except IOError:
#             logging.error("IOError: Could not get current value from {f}".format(f=current_value_file))
#         except IndexError:
#             logging.error("IndexError: Could not get current value from {f}".format(f=current_value_file))
#         return values
#
#     @classmethod
#     def last_changed(cls):
#         return os.path.getmtime(value_log_file)
#
#     def get_log(self, days):
#         # if mydebug.TEMP_TEST == 0:
#         file_name = value_log_file
#         # else:
#         #    file_name = test_temp_file
#
#         try:
#             with open(file_name, 'r') as f:
#                 log = f.read().split('\n')
#         except IOError:
#             log = "error"
#
#         index = 0
#         day_count = 0
#         last_day = None
#         for index in range(len(log)-1, -1, -1):
#             try:
#                 line = log[index].strip(',')
#                 if len(line) > 5:
#                     fields = line.split(',')
#                     temps = fields[5:]
#                     for t in temps:
#                         self.update_min_max_values(float(t))
#                     day = fields[2]
#                     if day != last_day:
#                         if last_day is not None:
#                             day_count += 1
#                         last_day = day
#             except IndexError:
#                 logging.error("Index error in log file {line}".format(line=log[index]))
#             except ValueError:
#                 logging.error("Value error in log file {line}".format(line=log[index]))
#
#             if day_count >= days:
#                 break
#
#         ret_lines = log[(index+1):]
#
#         return ret_lines


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
#        out.append(u"{name:s}:{temp:s}\u00B0".format(name=name, temp=value))
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


# class Temp():
#
#     def __init__(self):
#         if mydebug.TEST == 0:
#             os.system('modprobe w1-gpio')
#             os.system('modprobe w1-therm')
#
#         self.temp_sensor1 = "/sys/bus/w1/devices/28-0014117fb1ff/w1_slave"
#         self.temp_sensor2 = "/sys/bus/w1/devices/28-00000676eb5f/w1_slave"
#
#         self.room_sensor = self.temp_sensor1
#         self.tank_sensor = self.temp_sensor2
#
#         self.room_temp = 0
#         self.tank_temp = 0
#
#         self.lines = ''
#         self._stop = False
#
#
#     def get_temp_raw(self, sensor):
#         if mydebug.TEST == 0:
#             f = open(sensor, 'r')
#             self.lines = f.readlines()
#             f.close()
#         else:
#             lines = []
#             lines.append("76 01 55 00 7f ff 0c 10 ee : crc=ee YES")
#             lines.append("76 01 55 00 7f ff 0c 10 ee t=23375")
#             self.lines = lines
#         return self.lines
#
#     def get_tank_temp(self):
#         return self.tank_temp
#
#     def get_room_temp(self):
#         return self.room_temp
#
#     def get_all(self):
#         room_temp = self.get_room_temp()
#         tank_temp = self.get_tank_temp()
#         output = u"Room:{temp1:2.3f}\u00B0    Tank:{temp2:2.3f}\u00B0".format(temp1=room_temp, temp2=tank_temp)
#         return output
#
#
#     def read_temp(self, sensor):
#         if mydebug.TEST != 0:
#             return 20.1
#         else:
#             lines = self.get_temp_raw(sensor)
#             while lines[0].strip()[-3:] != 'YES':
#                 time.sleep(0.2)
#                 lines = self.get_temp_raw(sensor)
#
#             temp_output = lines[1].find('t=')
#             if temp_output != -1:
#                 temp_string = lines[1].strip()[temp_output+2:]
#                 temp_c = float(temp_string) / 1000.0
#                 return temp_c
#
#     def start(self):
#         thread = threading.Thread(target=self.task)
#         thread.start()
#
#     def stop(self):
#         self._stop = True
#
#     def get_log(self):
#         f = None
#         try:
#             f = open('/var/log/temp.txt', 'r')
#             log = f.read()
#         except:
#             log = "error"
#         finally:
#             if f is not None:
#                 f.close()
#         return log
#
#
#
#     def task(self):
#         last_min = 1
#         while not self._stop:
#             n = datetime.datetime.now()
#
#             self.room_temp = self.read_temp(self.room_sensor)
#             self.tank_temp = self.read_temp(self.tank_sensor)
#
#             output = u"{date:s}   Room:{temp1:2.3f}\u00B0    Tank:{temp2:2.3f}\u00B0".\
#                 format(date=n.strftime('%d/%b %H:%M'), temp1=self.room_temp, temp2=self.tank_temp)
#
#             outputln = output + u"\n"
#
#             print n.minute
#             if n.minute < last_min:
#                 print "hello\n"
#                 try:
#                     f = open('/var/log/temp.txt', 'a')
#                     f.write(outputln.encode('utf8'))
#                 except:
#                     e = sys.exc_info()[0]
#                     print e
#                     print "\n"
#                 finally:
#                     f.close()
#                 try:
#                     date = "{a},{b},{c},{d},{e}".format(a=n.year,b=n.month-1,c=n.day,d=n.hour,e=n.minute)
#                     f = open('/var/log/temp2.txt', 'a')
#                     output2 = u"[new Date({date:s}),{temp1:2.3f},{temp2:2.3f}],\n".\
#                         format(date=date, temp1=self.room_temp, temp2=self.tank_temp)
#                     f.write(output2)
#                 except:
#                     e = sys.exc_info()[0]
#                     print e
#                     print "\n"
#                 finally:
#                     f.close()
#
#             print output.encode('utf8')
#             last_min = n.minute
#             q = 0
#             while q < 60 and not self._stop:
#                 time.sleep(1)
#                 q += 1
#
#         print "stopping_1"
#
#
# def main():
#     setup_log()
#     logging.info("Started recording temps")
#     # tr = TempRecorder()
#     # tr.start()
#     # running = True
#     # while running:
#     #     try:
#     #         time.sleep(60)
#     #         # for _ in range(60):
#     #         #     if running:
#     #         #         time.sleep(1)
#     #         if running and tr.stopped:
#     #             logging.error("Restarting temp recorder task")
#     #             tr.start()
#     #     except KeyboardInterrupt:
#     #         print("\nCtrl-C  KeyboardInterrupt\n")
#     #         running = False
#     #         tr.stop()
#     #
#     # logging.info("Stopped recording temps")
#
#
# if __name__ == "__main__":
#     #    log,a,b = get_temp_log(5)
#     #    print log
#     #    print a,b
#     main()
