import tank
import cfg


class Graph(tank.Ticker):
    def __init__(self, config):
        super(Graph, self).__init__()
        self._name = config[cfg.ITEM_NAME]

    def init(self):
        pass

    def tick(self):
        pass
