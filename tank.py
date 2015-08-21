import logging
import os
# import tank_relayController
import time
# import tank_temp
import tank_cfg
import tank_log

def setup_log():
    default_log_dir = r'/var/log/tank/'
    default_logfile = default_log_dir+r'/tank.log'

    if not os.path.exists(default_log_dir):
        os.makedirs(default_log_dir)

    logging.basicConfig(filename=default_logfile, level=logging.DEBUG,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s')


def main():
    setup_log()
    logging.info("STARTED")
    tank_logger = tank_log.TankLog()

    cfg = tank_cfg.Config()

    for item in cfg.items:
        item[tank_cfg.ITEM_OBJECT].init()

    print ("TANK Monitor Running....")
    while True:
        time.sleep(5)
        for item in cfg.items:
            item[tank_cfg.ITEM_OBJECT].tick()
        tank_logger.tick()

    #
    # temp_recorder = tank_temp.TempRecorder()
    #
    # controller = tank_relayController.Controller()
    # controller.init_timers()
    #
    # temp_recorder.start()
    #
    # try:
    #     print ("TANK Monitor Running....")
    #     while controller.running and temp_recorder.running:
    #         time.sleep(60)
    # except KeyboardInterrupt:
    #     print("\nQUITTING\n")
    #     logging.warn("Ctrl-C")
    #     temp_recorder.stop()
    #     controller.stop()
    #     while controller.running or temp_recorder.running:
    #         controller.stop()
    #         temp_recorder.stop()
    #         time.sleep(0.1)


if __name__ == '__main__':
    main()
