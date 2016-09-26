#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This code was originally taken from https://github.com/zeuxisoo/python-pluginplot
import builtins as builtin
import imp
import os
import sys
import threading
import types


class Plugin(object):
    def __init__(self, name="Стандартное имя плагина (измени меня)", description=""):
        self.deferred_events = []  # events which plugin subsсribed on
        self.name = name
        self.description = description
        self.log = print
        self.log(name)

    # Event wrapper (executed on first start, and when everytime when you call it)
    def on_command(self, *commands):
        def wrapper(method):
            for command in commands:
                self.add_deferred_method(command, method)
            return method

        return wrapper

    def add_deferred_method(self, event_name, method):
        if event_name is None:
            raise ValueError("event_name can't be None")
        self.deferred_events.append(lambda target: target.add_event(event_name, method))

    # Register events for plugin
    def register(self, plugin):
        for deferred_event in self.deferred_events:
            deferred_event(plugin)


local_data = threading.local()

shared_space = types.ModuleType(__name__ + '.shared_space')
shared_space.__path__ = []
sys.modules[shared_space.__name__] = shared_space


class PluginSystem(object):
    def __init__(self, folder=None):
        self.events = {}  # key is event name, value is list of methods, those are subscribed to this method
        self.folder = folder

    def get_commands(self):
        return [command for command, event_hanlder in self.events.items()]

    def add_event(self, name, method):
        if name in self.events:  # if event is already initialized, append
            self.events[name].append(method)
        else:  # else create a new list
            self.events[name] = [method]

    def call_event(self, name, *args, **kwargs):
        events_ = self.events.get(name)
        if not events_:  # If there are not event handlers for our great event
            pass
        else:  # If there's a method handler (one or more)
            for event_ in events_:  # Loop over all of them
                event_(*args, **kwargs)  # Try to execute event with arguments
            return None

    def register_event(self, event):
        event.register(self)

    def register_events(self):
        if not self.folder:
            raise ValueError("Plugin.folder can not be None")
        else:
            self._init_plugin_files()

    def _init_plugin_files(self):
        for folder_path, folder_names, filenames in os.walk(self.folder):
            for filename in filenames:
                if filename.endswith('.py') and filename != "__init__.py":
                    # path/to/plugins/plugin/foo.py > plugin/foo.py > plugin.foo > shared_space.plugin.foo
                    full_plugin_path = os.path.join(folder_path, filename)
                    base_plugin_path = os.path.relpath(full_plugin_path, self.folder)
                    base_plugin_name = os.path.splitext(base_plugin_path)[0].replace(os.path.sep, '.')
                    module_source_name = "{0}.file_{1}".format(shared_space.__name__, base_plugin_name)
                    loaded_module = imp.load_module(
                        module_source_name,
                        *imp.find_module(os.path.splitext(filename)[0], [folder_path])
                    )
                    # TODO: Add support for any instance name of Plugin() class
                    self.register_event(loaded_module.plugin)

    def __enter__(self):
        local_data.plugin_stacks = [self]
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            local_data.plugin_stacks.pop()
        except:
            pass


def override_import(import_method):
    def wrapper(name, globals=None, locals=None, fromlist=None, level=0):
        # Try to get current plugin object
        try:
            plugin_object = local_data.plugin_stacks[-1]
        except (AttributeError, IndexError):
            plugin_object = None
        return import_method(name, globals, locals, fromlist, level)

    return wrapper


# Overrides default import method
builtin.__import__ = override_import(builtin.__import__)
