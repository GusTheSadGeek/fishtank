#!/usr/bin/python

import threading


class FishController:
    def __init__(self):
        self.relays = []
        self.temps = []
        pass

    def start(self):
        thread = threading.Thread(target=self.task)
        thread.start()

    def task(self):
        pass
