import ConfigParser
import tank_relayController
import timer
import tank_temp

RELAY_TYPE = 0
TIMER_TYPE = 1
TEMP_TYPE = 2
DIST_TYPE = 3
UNKNOWN_TYPE = 99

ITEM_NAME = 'name'
ITEM_TYPE = 'type'
ITEM_PIN = 'pin'
ITEM_ONVAL = 'onvalue'
ITEM_OFFVAL = 'offvalue'
ITEM_CONTROLLEDBY = 'controlledby'
ITEM_CONTROLS = 'controls'
ITEM_SENSOR = 'sensor'
ITEM_GRAPH = 'graph'
ITEM_LOGCOL = 'logcol'
ITEM_OBJECT = 'object'


class Instances(object):
    """
    Borg (singleton) class
    """
    __shared_state = {}

    def __init__(self):
        self.__dict__ = self.__shared_state
        if '_first_time' not in self.__dict__:
            self._first_time = False
            self.relays = None
            self.timers = None
            self.temps = None
            self.dists = None


class Config(object):
    """
    Borg (singleton) class
    """
    __shared_state = {}

    def __init__(self, file_name='tank.cfg'):
        self.__dict__ = self.__shared_state
        if '_first_time' not in self.__dict__:
            self._first_time = False
            self._config_file = file_name
            self._config = None
            self._items = []
            # self._relays = []
            # self._temps = []
            # self._distances = []
            # self._timers = []
            self._temp_interval = 60
            self.load_config()

            self.parse_config()

    @property
    def temp_interval(self):
        return self._temp_interval

    @property
    def items(self):
        return self._items

    # @property
    # def relays(self):
    #     return self._relays
    #
    # @property
    # def temps(self):
    #     return self._temps
    #
    # @property
    # def timers(self):
    #     return self._timers
    #
    # @property
    # def distances(self):
    #     return self._distances

    def load_config(self):
        self._config = ConfigParser.RawConfigParser()
        self._config.read(self._config_file)

    def parse_config(self):
        sections = self._config.sections()
        for s in sections:
            if s.startswith('general'):
                self._temp_interval = self._config.getint('general', 'temp_interval')
            else:
                self._items.append(self.setup_item(s))

            # if s.startswith('relay'):
            #     self._relays.append(self.setup_relay(s))
            # if s.startswith('temp'):
            #     self._temps.append(self.setup_temp(s))
            # if s.startswith('timer'):
            #     self._timers.append(self.setup_timer(s))
            # if s.startswith('dist'):
            #     self._distances.append(self.setup_dist(s))

    def add_val(self, item, section, name):
        item[name] = None
        if self._config.has_option(section, name):
            item[name] = self._config.get(section, name)

    def add_val_float(self, item, section, name):
        item[name] = None
        if self._config.has_option(section, name):
            item[name] = self._config.getfloat(section, name)

    def add_val_int(self, item, section, name):
        item[name] = None
        if self._config.has_option(section, name):
            item[name] = self._config.getint(section, name)

    def setup_item(self, section):
        item_type = UNKNOWN_TYPE
        item = {
            ITEM_NAME: self._config.get(section, 'name')
        }

        self.add_val_int(item, section, ITEM_PIN)
        self.add_val_float(item, section, ITEM_ONVAL)
        self.add_val_float(item, section, ITEM_OFFVAL)
        self.add_val(item, section, ITEM_CONTROLLEDBY)
        self.add_val(item, section, ITEM_CONTROLS)
        self.add_val(item, section, ITEM_SENSOR)
        self.add_val(item, section, ITEM_GRAPH)
        self.add_val(item, section, ITEM_LOGCOL)

        if section.startswith('relay'):
            item_type = RELAY_TYPE
            item_object = tank_relayController.Relay(item)
        if section.startswith('temp'):
            item_type = TEMP_TYPE
            item_object = tank_temp.TempSensor(item)
        if section.startswith('timer'):
            item_type = TIMER_TYPE
            item_object = timer.Timer(item)
        # if section.startswith('dist'):
        #     item_type = DIST_TYPE
        #     item_object = tank_relayController.Relay(item)

        item[ITEM_TYPE] = item_type
        if item_object is not None:
            item[ITEM_OBJECT] = item_object
        else:
            item = None

        return item

    def get_item(self, name):
        for i in self.items:
            if i[ITEM_NAME] == name:
                return i[ITEM_OBJECT]


    # def parse_config2(self):
    #     sections = self._config.sections()
    #     for s in sections:
    #         if s.startswith('relay'):
    #             self._relays.append(self.setup_relay(s))
    #         if s.startswith('temp'):
    #             self._temps.append(self.setup_temp(s))
    #         if s.startswith('timer'):
    #             self._timers.append(self.setup_timer(s))
    #         if s.startswith('dist'):
    #             self._distances.append(self.setup_dist(s))
    #         if s.startswith('general'):
    #             self._temp_interval = self._config.getint('general','temp_interval')
    #
    # def setup_relay(self, section):
    #     relay = {
    #         'pin': self._config.getint(section, 'pin'),
    #         'name': self._config.get(section, 'name'),
    #         'controller': self._config.get(section, 'controlledby')
    #     }
    #     if self._config.has_option(section, 'ontemp'):
    #         relay['ontemp'] = self._config.getfloat(section, 'ontemp')
    #     if self._config.has_option(section, 'offtemp'):
    #         relay['offtemp'] = self._config.getfloat(section, 'offtemp')
    #     return relay
    #
    # def setup_temp(self, section):
    #     temp = {
    #         'name': self._config.get(section, 'name'),
    #         'sensor': self._config.get(section, 'sensor'),
    #         'controls': self._config.get(section, 'controls')
    #     }
    #     return temp
    #
    # def setup_timer(self, section):
    #     timer = {
    #         'name':  self._config.get(section, 'name'),
    #         'controls': self._config.get(section, 'controls')
    #     }
    #     return timer
    #
    # def setup_dist(self, section):
    #     print section
    #     print self.__first_time
    #     return None


def main():
    cfg = Config()
    # print cfg.relays
    # print cfg.timers
    # print cfg.temps


if __name__ == "__main__":
    main()
