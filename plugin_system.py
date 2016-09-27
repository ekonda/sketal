# This code was originally taken from https://github.com/zeuxisoo/python-pluginplot
import builtins as builtin
import imp
import os
import sys
import threading
import types

from say import say, fmt


class Plugin(object):
    def __init__(self, name="Стандартное имя плагина (измени меня)", description=""):
        self.deferred_events = []  # events which plugin subsсribed on
        self.name = name
        self.description = description
        self.first_command = ''
        say(name)

    def log(self, message):
        with say.settings(prefix=fmt('Плагин {self.name} -> ')):
            say(message)

    # Декоратор события (запускается при первом запуске)
    def on_command(self, *commands):
        def wrapper(function):
            if commands:  # Если написали, какие команды используются
                # Первая команда - отображается в списке команд (чтобы много команд не было)
                self.first_command = commands[0]
                for command in commands:
                    self.add_deferred_func(command, function)
            else:  # Если нет - используем имя плагина в качестве команды (в нижнем регистре)
                self.add_deferred_func(self.name.lower(), function)
            return function

        return wrapper

    def add_deferred_func(self, command, function):
        if command is None:
            raise ValueError("command can't be None")
        self.deferred_events.append(lambda pluginsystem_object: pluginsystem_object.add_command(command, function))

    # Register events for plugin
    def register(self, plugin_system_object):
        for deferred_event in self.deferred_events:
            deferred_event(plugin_system_object)


local_data = threading.local()

shared_space = types.ModuleType(__name__ + '.shared_space')
shared_space.__path__ = []
sys.modules[shared_space.__name__] = shared_space


class PluginSystem(object):
    def __init__(self, folder=None):
        self.commands = {}
        self.folder = folder
        self.plugins = []

    def get_plugins(self):
        return [plugin for plugin in self.plugins]

    def add_command(self, name, function):
        # если уже есть хоть 1 команда, добавляем к списку
        if name in self.commands:
            self.commands[name].append(function)
        # если нет, создаём новый список
        else:
            self.commands[name] = [function]

    def call_command(self, command_name, *args, **kwargs):
        # получаем фн-ции команд для этой команды (несколько плагинов МОГУТ обрабатывать одну команду)
        commands_ = self.commands.get(command_name)
        # если нету плагинов, которые готовы обработать нашу команду
        if not commands_:
            pass
        # Если есть функции, которые могут обработать нашу команду
        else:
            # Проходимся по всем ним
            for command_function in commands_:
                # Запускаем с аргументами
                command_function(*args, **kwargs)
            return None

    def register_plugin(self, plugin_object):
        plugin_object.register(self)

    def register_commands(self):
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
                    self.plugins.append(loaded_module.plugin)
                    self.register_plugin(loaded_module.plugin)

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
