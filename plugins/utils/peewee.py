from handler.base_plugin import BasePlugin

import peewee
import peewee_async

""" peewee_async
Docs: https://peewee-async.readthedocs.io/en/latest/

peewee
Docs: http://docs.peewee-orm.com/en/latest/
"""


class PeeweePlugin(BasePlugin):
    __slots__ = ("database", "manager", "set_manager")

    def __init__(self, dbhost, dbname, dbuser, dbpassword, dbport, custom_driver=None, set_manager=False, **kwargs):
        """Adds self to messages and event's `data` field.
        Through this instance you can access peewee_async.Manager instance (data["peewee_async"].manager).
        This plugin should be included first!
        """

        super().__init__()

        self.set_manager = set_manager

        # You can replace PostgresqlDatabase with MysqlDatabase or pass driver you want tot use in custom_driver argument

        if custom_driver is None:
            driver = peewee_async.PostgresqlDatabase
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
        msg.data["peewee_async"] = self

    async def global_before_event_checks(self, evnt):
        evnt.data["peewee_async"] = self
