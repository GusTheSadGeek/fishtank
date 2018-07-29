import ConfigParser
import relay
import timer
import temp_sensor
import graph
import dist_sensor
import os
import logging

RELAY_TYPE = 0
TIMER_TYPE = 1
TEMP_TYPE = 2
DIST_TYPE = 3
GRAPH_TYPE = 4
UNKNOWN_TYPE = 99

# General
ITEM_CONTROLSTATE = 'controlstate'
ITEM_LOGINTERVAL = 'log_interval'
ITEM_LOGLEVEL = 'loglevel'

# items
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
ITEM_GRAPHTYPE = 'type'
ITEM_GRAPHCOLOURS = 'colours'
ITEM_GPOS = 'gpos'
ITEM_LOGCOL = 'logcol'
ITEM_HEIGHT = 'height'
ITEM_SCALE = 'scale'
ITEM_YAXIS = 'yaxis'
ITEM_ALWAYSACTIVE = 'alwaysactive'
ITEM_OBJECT = 'object'
ITEM_ZERO = 'zero'

ITEM_INSTAPUSH_ID = 'instapushid'
ITEM_INSTAPUSH_SECRET = 'instapushsecret'
ITEM_ALERT_MIN = 'alertmin'
ITEM_ALERT_MAX = 'alertmax'


class ConfigSection(object):
    def __init__(self, section, config):
        self.section = section
        self.config = config
        self._type = None
        self._object = None

    def trygetint(self, name, default=None):
        if self.config.has_option(self.section, name):
            return self.config.getint(self.section, name)
        else:
            return default

    def trygetfloat(self, name, default=None):
        if self.config.has_option(self.section, name):
            return self.config.getfloat(self.section, name)
        else:
            return default

    def tryget(self, name, default=None):
        if self.config.has_option(self.section, name):
            return self.config.get(self.section, name)
        else:
            return default

    @property
    def name(self):
        return self.tryget(ITEM_NAME)

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, _type):
        self._type = _type

    @property
    def object(self):
        return self._object

    @object.setter
    def object(self, _object):
        self._object = _object

    @property
    def pin(self):
        return self.trygetint(ITEM_PIN)

    @property
    def trig_pin(self):
        return self.trygetint(ITEM_TRIGPIN)

    @property
    def echo_pin(self):
        return self.trygetint(ITEM_ECHOPIN)

    @property
    def tank_depth(self):
        return self.trygetfloat(ITEM_TANKDEPTH)

    @property
    def onvalue(self):
        return self.trygetfloat(ITEM_ONVAL)

    @property
    def offvalue(self):
        return self.trygetfloat(ITEM_OFFVAL)

    @property
    def onvalue2(self):
        return self.trygetfloat(ITEM_ONVAL2)

    @property
    def offvalue2(self):
        return self.trygetfloat(ITEM_OFFVAL2)

    @property
    def controlledby(self):
        return self.tryget(ITEM_CONTROLLEDBY)

    @property
    def controlledby_and(self):
        return self.tryget(ITEM_CONTROLLEDBY_AND)

    @property
    def controlledby_or(self):
        return self.tryget(ITEM_CONTROLLEDBY_OR)

    @property
    def controls(self):
        return self.tryget(ITEM_CONTROLS)

    @property
    def sensor(self):
        return self.tryget(ITEM_SENSOR)

    @property
    def graph(self):
        return self.tryget(ITEM_GRAPH)

    @property
    def graph_type(self):
        return self.tryget(ITEM_GRAPHTYPE)

    @property
    def graph_colours(self):
        return self.tryget(ITEM_GRAPHCOLOURS)

    @property
    def gpos(self):
        return self.tryget(ITEM_GPOS)

    @property
    def logcol(self):
        return self.trygetint(ITEM_LOGCOL)

    @property
    def height(self):
        return self.trygetfloat(ITEM_HEIGHT)

    @property
    def scale(self):
        return self.trygetint(ITEM_SCALE)

    @property
    def zerobased(self):
        return self.trygetint(ITEM_ZERO, 0)

    @property
    def yaxis(self):
        return self.tryget(ITEM_YAXIS)

    @property
    def always_active(self):
        return self.trygetint(ITEM_ALWAYSACTIVE, 0)

    @property
    def alert_min(self):
        return self.trygetfloat(ITEM_ALERT_MIN, -999.0)

    @property
    def alert_max(self):
        return self.trygetfloat(ITEM_ALERT_MAX, 999.0)

###################

    @property
    def control_state(self):
        return self.config.get('general', ITEM_CONTROLSTATE)


class Config(object):
    """
    Borg (singleton) class
    """
    __shared_state = {}

    def __init__(self, file_name='/home/pi/git/fishtank/tank.cfg'):
        self.__dict__ = self.__shared_state
        if '_first_time' not in self.__dict__:
            self._first_time = False
            self._config_file = file_name
            self._config_file_time = None
            self._savedcfg = None
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

    def tick(self):
        filetime = os.path.getmtime(self._config_file)
        if filetime != self._config_file_time:
            self.load_config()

    def trygetint(self, section, name, default=None):
        if self._config.has_option(section, name):
            return self._config.getint(section, name)
        else:
            return default

    def trygetfloat(self, section, name, default=None):
        if self._config.has_option(section, name):
            return self._config.getfloat(section, name)
        else:
            return default

    def tryget(self, section, name, default=None):
        if self._config.has_option(section, name):
            return self._config.get(section, name)
        else:
            return default

    @property
    def config(self):
        return self._config

    @property
    def log_level(self):
        return self.trygetint('general', ITEM_LOGLEVEL, logging.WARNING)

    @property
    def log_interval(self):
        return self.trygetint('general', ITEM_LOGINTERVAL, 900)  # 15 min default

    @property
    def instapush_app_id(self):
        return self.config.get('general', ITEM_INSTAPUSH_ID)

    @property
    def instapush_secret(self):
        return self.config.get('general', ITEM_INSTAPUSH_SECRET)

    @property
    def control_state(self):
        return self._config.get('general', ITEM_CONTROLSTATE)

    @control_state.setter
    def control_state(self, new_state):
        self._config.set('general', ITEM_CONTROLSTATE, new_state)
        self.save_config()

    @property
    def items(self):
        return self._items

    @property
    def configurable_items(self):
        return self._config.items('config')

    @property
    def graphed_items(self):
        if self._graph_items is None:
            self._graph_items = []
            for i in self._items:
                if i.graph is not None:
                    self._graph_items.append(i)
        return self._graph_items

    @property
    def graphs_types(self):
        if self._graph_types is None:
            self._graph_types = []
            for i in self._items:
                g = i.graph
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
            if i.type == t:
                items.append(i)
        return items

    def set_config_data(self, data):
        for section, key, val in data:
            self._config.set(section, key, val)
        self.save_config()

    def save_config(self):
        with open(self._config_file, 'w') as fp:
            self._config.write(fp)
        self._config_file_time = os.path.getmtime(self._config_file)

    def load_config(self):
        if self._config is None:
            self._config = ConfigParser.RawConfigParser()
        self._config.read(self._config_file)
        if not self._config.has_section('general'):
            self._config.add_section('general')
        if not self._config.has_option('general', ITEM_CONTROLSTATE):
            self._config.set('general', ITEM_CONTROLSTATE)
            self.save_config()

    def parse_config(self):
        sections = self._config.sections()
        for s in sections:
            if s.startswith('general'):
                pass
            else:
                item = self.setup_item(s)
                if item is not None:
                    self._items.append(item)

    def setup_item(self, section):
        cfg_sec = ConfigSection(section, self._config)

        if section.startswith('relay'):
            cfg_sec.type = RELAY_TYPE
            cfg_sec.object = relay.Relay(cfg_sec)
        if section.startswith('temp'):
            cfg_sec.type = TEMP_TYPE
            cfg_sec.object = temp_sensor.TempSensor(cfg_sec)
        if section.startswith('timer'):
            cfg_sec.type = TIMER_TYPE
            cfg_sec.object = timer.Timer(cfg_sec)
        if section.startswith('dist'):
            cfg_sec.type = DIST_TYPE
            cfg_sec.object = dist_sensor.DistSensor(cfg_sec)
        if section.startswith('graph'):
            cfg_sec.type = GRAPH_TYPE
            cfg_sec.object = graph.Graph(cfg_sec)

        if cfg_sec.type is None:
            cfg_sec = None

        return cfg_sec

    def get_item(self, name):
        for i in self.items:
            if i.name == name:
                return i.object


def main():
    cfg = Config()
#    cfg.write_saved_state()
    cfg.control_state = 27
    print cfg
    # print cfg.timers
    # print cfg.temps


if __name__ == "__main__":
    main()
