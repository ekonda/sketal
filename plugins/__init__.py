from handler.base_plugin import BasePlugin

import importlib
import pkgutil
import sys, os

__all__ = []


def join(*es):
    return os.sep.join(es)

def load_plugins(path):
    for p, ds, fs in os.walk(path):
        for f in fs:
            if not f.endswith(".py") or f.startswith("_"):
                continue

            module = join(p, f).replace(os.sep, ".")[:-3]

            try:
                exec(f"global m; import {module} as m")

            except AttributeError:
                print("Strange module: " + str(module))
                continue

            for en in dir(m):
                if en in __all__:
                    continue

                e = m.__getattribute__(en)

                if isinstance(e, type) and issubclass(e, BasePlugin) and e.__module__ == m.__name__:
                    exec(f"global {en}; from {module} import {en}")
                    __all__.append(en)

load_plugins("plugins")
