from handler.base_plugin import BasePlugin

import importlib
import pkgutil
import sys, os

__all__ = []


def join(*es):
    return os.sep.join(es)

def import_plugins(package):
    if isinstance(package, str):
        package = importlib.import_module(package)

    for loader, name, is_pkg in pkgutil.walk_packages(package.__path__):
        full_name = package.__name__ + '.' + name

        module = importlib.import_module(full_name)

        for name in dir(module):
            if name[0] == "_":
                continue

            e = module.__getattribute__(name)

            if e in __all__:
                continue

            if isinstance(e, type) and issubclass(e, BasePlugin) and e.__module__ == module.__name__:
                __all__.append(e.__name__)
                globals()[e.__name__] = e

        if is_pkg:
            import_plugins(full_name)

import_plugins(__name__)
