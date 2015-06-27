#!/usr/bin/python

import os
import time
import datetime
import threading

testing = 0


class Temp():

    def __init__(self):
        if not testing:
            os.system('modprobe w1-gpio')
            os.system('modprobe w1-therm')

        self.temp_sensor1 = "/sys/bus/w1/devices/28-0014117fb1ff/w1_slave"
        self.temp_sensor2 = "/sys/bus/w1/devices/28-00000676eb5f/w1_slave"

        self.room_sensor = self.temp_sensor1
        self.tank_sensor = self.temp_sensor2

        self.room_temp = 0
        self.tank_temp = 0

        self.lines = ''
        self._stop = False


    def get_temp_raw(self, sensor):
        f = open(sensor, 'r')
        self.lines = f.readlines()
        f.close()
        return self.lines

    def get_tank_temp(self):
        return self.tank_temp

    def get_room_temp(self):
        return self.room_temp

    def get_all(self):
        room_temp = self.get_room_temp()
        tank_temp = self.get_tank_temp()
        output = u"Room:{temp1:2.3f}\u00B0    Tank:{temp2:2.3f}\u00B0".format(temp1=room_temp, temp2=tank_temp)
        return output


    def read_temp(self, sensor):
        if testing:
            return 20.1
        else:
            lines = self.get_temp_raw(sensor)
            while lines[0].strip()[-3:] != 'YES':
                time.sleep(0.2)
                lines = self.get_temp_raw(sensor)

            temp_output = lines[1].find('t=')
            if temp_output != -1:
                temp_string = lines[1].strip()[temp_output+2:]
                temp_c = float(temp_string) / 1000.0
                return temp_c

    def start(self):
        thread = threading.Thread(target=self.task)
        thread.start()

    def stop(self):
        self._stop = True

    def get_log(self):
        f = None
        try:
            f = open('/var/log/temp.txt', 'r')
            log = f.read()
        except:
            log = "error"
        finally:
            if f is not None:
                f.close()
        return log

    def get_log2(self):
        f = None
        try:
            f = open('/var/log/temp2.txt', 'r')
            log = f.read()
        except:
            log = "error"
        finally:
            if f is not None:
                f.close()
        return log


    def task(self):
        last_min = 1
        while not self._stop:
            n = datetime.datetime.now()

            self.room_temp = self.read_temp(self.room_sensor)
            self.tank_temp = self.read_temp(self.tank_sensor)

            output = u"{date:s}   Room:{temp1:2.3f}\u00B0    Tank:{temp2:2.3f}\u00B0".\
                format(date=n.strftime('%d/%b %H:%M'), temp1=self.room_temp, temp2=self.tank_temp)

            outputln = output + u"\n"

            print n.minute
            if n.minute < last_min:
                print "hello\n"
                try:
                    f = open('/var/log/temp.txt', 'a')
                    f.write(outputln.encode('utf8'))
                except:
                    e = sys.exc_info()[0]
                    print e
                    print "\n"  
                finally:
                    f.close()
                try:
                    date = "{a},{b},{c},{d},{e}".format(a=n.year,b=n.month-1,c=n.day,d=n.hour,e=n.minute)
                    f = open('/var/log/temp2.txt', 'a')
                    output2 = u"[new Date({date:s}),{temp1:2.3f},{temp2:2.3f}],\n".\
                        format(date=date, temp1=self.room_temp, temp2=self.tank_temp)
                    f.write(output2)
                except:
                    e = sys.exc_info()[0]
                    print e
                    print "\n"  
                finally:
                    f.close()

            print output.encode('utf8')
            last_min = n.minute
            q = 0
            while q < 60 and not self._stop:
                time.sleep(1)
                q += 1

        print "stopping_1"
