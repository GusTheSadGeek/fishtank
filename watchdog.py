import threading
import time
import logging
import os


running = True
time_stamp = time.time()
thread = None
debug_info = ''


def get_mac_addr():
    # noinspection PyBroadException
    try:
        mac = open('/sys/class/net/eth0/address').read().strip()
    except:
        mac = ''
    finally:
        pass
    return mac


def reboot_allowed():
    mac = get_mac_addr()
    if mac == 'b8:27:eb:0c:1b:07':
        return True
    return False


def set_debug_info(info):
    global debug_info
    debug_info = info


def start_watchdog():
    global thread
    thread = threading.Thread(target=watcher)
    thread.start()


def stop_watchdog():
    global running
    running = False


def still_alive():
    global time_stamp
    time_stamp = time.time()


def watcher():
    global time_stamp
    still_alive()
    while running:
        now = time.time()
        diff = now - time_stamp
        if diff > 50:
            logging.fatal("50+ seconds since still_alive received - rebooting " + str(diff))
            reboot()
        elif diff > 40:
            logging.critical("40+ seconds since still_alive received " + str(diff))
        elif diff > 30:
            logging.warning("30+ seconds since still_alive received " + str(diff))
        elif diff > 20:
            logging.warning("20+ seconds since still_alive received " + str(diff))
        for _ in range(5):
            time.sleep(1)
            if not running:
                return


def reboot():
    logging.fatal(debug_info)
    logging.fatal("rebooting - BYE !")
    time.sleep(1)
    if reboot_allowed():
        print "reboot"
        os.system("reboot")
