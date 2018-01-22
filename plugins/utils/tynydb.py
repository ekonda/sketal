from handler.base_plugin import BasePlugin


from tinydb import TinyDB, Query
from tinydb.storages import JSONStorage
from tinydb.middlewares import CachingMiddleware

""" TinyDB
Docs: http://tinydb.readthedocs.io/en/latest/

General sample usage:
>>> User = Query()
>>> db.insert({'name': 'John', 'age': 22})
>>> db.search(User.name == 'John')
[{'name': 'John', 'age': 22}]
"""


class TinyDBPlugin(BasePlugin):
    __slots__ = ("tinydb")

    def __init__(self):
        """Adds self to messages and event's `data` field.
        Through this instance you can access TinyDB instance (data["tinydbproxy"].tinydb).
        This plugin should be included first!
        """

        super().__init__()

        self.tinydb = TinyDB(path=self.get_path("tinydb_database.json"), storage=CachingMiddleware(JSONStorage))

    def get_user(self, user_id):
        User = Query()

        user = self.tinydb.get(User.user_id == user_id)

        return user["data"] if user else {}

    def save_user(self, user_id, data):
        User = Query()

        if not self.tinydb.update({'user_id': user_id, 'data': data}, User.user_id == user_id):
            self.tinydb.insert({'user_id': user_id, 'data': data})

    def delete_user(self, user_id):
        User = Query()

        self.tinydb.remove(User.user_id == user_id)

    async def global_before_message_checks(self, msg):
        msg.meta["tdb"] = self

    async def global_before_event_checks(self, evnt):
        evnt.meta["tdb"] = self
