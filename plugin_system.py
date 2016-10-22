# This code was originally taken from https://github.com/zeuxisoo/python-pluginplot
import imp
import os
import sys
import threading
import traceback
import types
import hues
from os.path import isfile


class Plugin(object):
    def __init__(self, name="Стандартное имя плагина (измени меня)", description=""):
        self.deferred_events = []  # events which plugin subsсribed on
        self.name = name
        self.description = description
        self.first_command = ''
        hues.warn(self.name)

    def log(self, message: str):
        hues.info('Плагин {name} -> {message}'.format(name=self.name, message=message))

    # Декоратор события (запускается при первом запуске)
    def on_command(self, *commands, all_commands=False):
        def wrapper(function):
            if commands:  # Если написали, какие команды используются
                # Первая команда - отображается в списке команд (чтобы не было много команд не было)
                self.first_command = commands[0]
                for command in commands:
                    self.add_deferred_func(command, function)
            elif not all_commands:  # Если нет - используем имя плагина в качестве команды (в нижнем регистре)
                self.add_deferred_func(self.name.lower(), function)
            # если команд нет, плагин будет реагировать на ВСЕ команды
            else:
                self.add_deferred_func('', function)
            return function

        return wrapper

    def add_deferred_func(self, command, function):
        if command is None:
            raise ValueError("Command can not be None")
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
        self.plugins = set()

    def get_plugins(self) -> set:
        return self.plugins

    def add_command(self, name, function):
        # если уже есть хоть 1 команда, добавляем к списку
        if name in self.commands:
            self.commands[name].append(function)
        # если нет, создаём новый список
        else:
            self.commands[name] = [function]

    async def call_command(self, command_name, *args, **kwargs):
        # Получаем функции команд для этой команды (несколько плагинов МОГУТ обрабатывать одну команду)
        commands_ = self.commands.get(command_name)

        # Если нет плагинов, которые готовы обработать нашу команду
        if not commands_:
            return

        # Если есть плагины, которые могут обработать нашу команду
        for command_function in commands_:
            # Запускаем с аргументами
            await command_function(*args, **kwargs)

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
                    try:
                        loaded_module = imp.load_module(
                            module_source_name,
                            *imp.find_module(os.path.splitext(filename)[0], [folder_path])
                        )
                    # Если при загрузке плагина какая-либо ошибка
                    except Exception:
                        result = traceback.format_exc()
                        # если файла нет - создаём
                        if not isfile('log.txt'):
                            open('log.txt', 'w').close()

                        with open('log.txt', 'a') as log:
                            log.write(result)
                        continue
                    try:
                        self.plugins.add(loaded_module.plugin)
                        self.register_plugin(loaded_module.plugin)
                    # Если возникла ошибка - значит плагин не имеет атрибута plugin
                    except AttributeError:
                        continue

    def __enter__(self):
        local_data.plugin_stacks = [self]
        return self

    def __exit__(self, exc_type, exc_value, tbc):
        try:
            local_data.plugin_stacks.pop()
        except Exception:
            pass
