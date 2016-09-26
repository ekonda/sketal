#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This code was originally taken from https://github.com/zeuxisoo/python-pluginplot
import logging
import time

class Plugin(object):
    def __init__(self, name="Plugin(changeme)", description="", version=""):
        self.deferred_events = []  #events which plugin substribed on
        self.name = name
        self.description = description
        self.version = version
        self.version_prefix = "" if version == "" else "v"  # If there's version - let's append prefix
        self.logger = logging.getLogger("{name}{{{time}}}".format(name=self.name, time=time.strftime("%H:%M:%S")))
        self.logger.setLevel(logging.INFO)
        self.log = self.logger.info

    # Event wrapper (executed on first start, one time only)
    def event(self, event_name=None):
        def wrapper(method):
            self.add_deferred_method(event_name, method)
            return method

        return wrapper

    def add_deferred_method(self, event_name, method):
        if event_name is None:
            raise ValueError('event_name can\'t be None')
        self.deferred_events.append(lambda target: target.add_event(event_name, method))

    # Register events for plugin
    def register(self, plugin):
        for deferred_event in self.deferred_events:
            deferred_event(plugin)
