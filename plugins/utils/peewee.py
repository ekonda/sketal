from handler.base_plugin import BasePlugin

import peewee_async


""" peewee_async
Docs: https://peewee-async.readthedocs.io/en/latest/

peewee
Docs: http://docs.peewee-orm.com/en/latest/
"""

"""Possible `custom_driver` values is any peewee_async.* driver or "PostgreSQL" or "MySQL"
"""


class PeeweePlugin(BasePlugin):
    __slots__ = ("database", "manager", "set_manager")

    def __init__(self, dbhost, dbname, dbuser, dbpassword, dbport=None, custom_driver=None, set_manager=True, **kwargs):
        """Adds self to messages and event's `data` field.
        Through this instance you can access peewee_async.Manager instance (data["peewee_async"].manager).
        This plugin should be included first!
        """

        super().__init__()

        self.set_manager = set_manager

        if custom_driver is None or custom_driver == "PostgreSQL":
            driver = peewee_async.PostgresqlDatabase
            if dbport is None: dbport = 5432

        elif custom_driver == "MySQL":
            driver = peewee_async.MySQLDatabase
            if dbport is None: dbport = 3306

        else:
            driver = custom_driver

        if isinstance(dbport, str):
            try:
                dbport = int(dbport)
            except ValueError:
                raise ValueError("Port is wrong!")

        self.database = driver(dbname, user=dbuser, password=dbpassword, host=dbhost, port=dbport, **kwargs)
        self.manager = peewee_async.Manager(self.database)
        self.database.set_allow_sync(False)

    def initiate(self):
        if self.set_manager:
            for plugin in self.handler.plugins:
                if hasattr(plugin, "pwmanager"):
                    plugin.pwmanager = self.manager

    async def global_before_message_checks(self, msg):
        msg.meta["peewee_async"] = self

    async def global_before_event_checks(self, evnt):
        evnt.meta["peewee_async"] = self
