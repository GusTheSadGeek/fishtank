import ConfigParser
import relay
import timer
import temp_sensor
import graph
import dist_sensor

RELAY_TYPE = 0
TIMER_TYPE = 1
TEMP_TYPE = 2
DIST_TYPE = 3
GRAPH_TYPE = 4
UNKNOWN_TYPE = 99

ITEM_NAME = 'name'
ITEM_TYPE = 'type'
ITEM_PIN = 'pin'
ITEM_TRIGPIN = 'trig_pin'
ITEM_ECHOPIN = 'echo_pin'
ITEM_TANKDEPTH = 'tank_depth'
ITEM_ONVAL = 'onvalue'
ITEM_OFFVAL = 'offvalue'
ITEM_ONVAL2 = 'onvalue2'
ITEM_OFFVAL2 = 'offvalue2'
ITEM_CONTROLLEDBY = 'controlledby'
ITEM_CONTROLLEDBY_AND = 'controlledbyand'
ITEM_CONTROLLEDBY_OR = 'controlledbyor'
ITEM_CONTROLS = 'controls'
ITEM_SENSOR = 'sensor'
ITEM_GRAPH = 'graph'
ITEM_LOGCOL = 'logcol'
ITEM_HEIGHT = 'height'
ITEM_SCALE = 'scale'
ITEM_YAXIS = 'yaxis'
ITEM_ALWAYSACTIVE = 'alwaysactive'
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
            self._temp_interval = 60
            self._graph_items = None
            self._graph_types = None
            self._relay_items = None
            self._timer_items = None
            self._temp_items = None
            self.load_config()

            self.parse_config()

    @property
    def temp_interval(self):
        return self._temp_interval

    @property
    def items(self):
        return self._items

    @property
    def graphed_items(self):
        if self._graph_items is None:
            self._graph_items = []
            for i in self._items:
                if i[ITEM_GRAPH] is not None:
                    self._graph_items.append(i)
        return self._graph_items

    @property
    def graphs_types(self):
        if self._graph_types is None:
            self._graph_types = []
            for i in self._items:
                g = i[ITEM_GRAPH]
                if g is not None:
                    if g not in self._graph_types:
                        self._graph_types.append(g)
        return self._graph_types

    @property
    def relay_items(self):
        if self._relay_items is None:
            self._relay_items = self.get_items(RELAY_TYPE)
        return self._relay_items

    @property
    def timer_items(self):
        if self._timer_items is None:
            self._timer_items = self.get_items(TIMER_TYPE)
        return self._timer_items

    @property
    def temp_items(self):
        if self._temp_items is None:
            self._temp_items = self.get_items(TEMP_TYPE)
        return self._temp_items

    @property
    def graph_items(self):
        if self._temp_items is None:
            self._temp_items = self.get_items(GRAPH_TYPE)
        return self._temp_items

    def get_items(self, t):
        items = []
        for i in self._items:
            if i[ITEM_TYPE] == t:
                items.append(i)
        return items

    def load_config(self):
        self._config = ConfigParser.RawConfigParser()
        self._config.read(self._config_file)

    def parse_config(self):
        sections = self._config.sections()
        for s in sections:
            if s.startswith('general'):
                self._temp_interval = self._config.getint('general', 'temp_interval')
            else:
                item = self.setup_item(s)
                if item is not None:
                    self._items.append(item)

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
        item_object = None
        item = {
            ITEM_NAME: self._config.get(section, 'name')
        }

        self.add_val_int(item, section, ITEM_PIN)
        self.add_val_int(item, section, ITEM_TRIGPIN)
        self.add_val_int(item, section, ITEM_ECHOPIN)
        self.add_val_int(item, section, ITEM_TANKDEPTH)
        self.add_val_int(item, section, ITEM_ALWAYSACTIVE)

        self.add_val_float(item, section, ITEM_ONVAL)
        self.add_val_float(item, section, ITEM_OFFVAL)
        self.add_val_float(item, section, ITEM_ONVAL2)
        self.add_val_float(item, section, ITEM_OFFVAL2)

        self.add_val(item, section, ITEM_CONTROLLEDBY)
        self.add_val(item, section, ITEM_CONTROLLEDBY_AND)
        self.add_val(item, section, ITEM_CONTROLLEDBY_OR)
        self.add_val(item, section, ITEM_CONTROLS)
        self.add_val(item, section, ITEM_SENSOR)
        self.add_val(item, section, ITEM_GRAPH)
        self.add_val(item, section, ITEM_LOGCOL)
        self.add_val(item, section, ITEM_HEIGHT)
        self.add_val(item, section, ITEM_SCALE)
        self.add_val(item, section, ITEM_YAXIS)

        if section.startswith('relay'):
            item_type = RELAY_TYPE
            item_object = relay.Relay(item)
        if section.startswith('temp'):
            item_type = TEMP_TYPE
            item_object = temp_sensor.TempSensor(item)
        if section.startswith('timer'):
            item_type = TIMER_TYPE
            item_object = timer.Timer(item)
        if section.startswith('dist'):
            item_type = DIST_TYPE
            item_object = dist_sensor.DistSensor(item)
        if section.startswith('graph'):
            item_type = GRAPH_TYPE
            item_object = graph.Graph(item)

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


def main():
    cfg = Config()
    print cfg
    # print cfg.timers
    # print cfg.temps


if __name__ == "__main__":
    main()
