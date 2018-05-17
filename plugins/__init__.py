from handler.base_plugin import BasePlugin, DEFAULTS

import importlib
import pkgutil
import sys, os

__all__ = ["DEFAULTS"]

def save_doc(e, full_name, file_name=None):
    with open(file_name, "a") as o:
        if o.tell() == 0:
            print("## Sketal's plugins", file=o)

        print("[**" + e.__name__ + "**" + " `[" +
            ".".join(full_name.split(".")[:-1]) + "]`](" +
                "/" + full_name.replace(".", "/") + ".py)", file=o)
        print("\n", file=o)

        desc = []
        for l in e.__init__.__doc__.splitlines():
            if l.strip():
                desc += [l.strip()]
        print("\n".join(desc), file=o)
        print("\n---", file=o)

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
                if "-wrplugins" in sys.argv:
                    save_doc(e, full_name, "PLUGINS.md")

                __all__.append(e.__name__)
                globals()[e.__name__] = e

        if is_pkg:
            import_plugins(full_name)

import_plugins(__name__)
