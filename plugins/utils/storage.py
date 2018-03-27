from handler.base_plugin import BasePlugin

import time

import motor.motor_asyncio


class StoragePlugin(BasePlugin):
    __slots__ = ("client", "database", "users", "chats", "inmemory")

    def __init__(self, host="localhost", port=27017, database="sketal_db",
            inmemory=False):
        """Allows users and chats to store persistent data with MongoDB or in
        memory. Both storages are siuated in `meta` as `data_user` and
        `data_chat` and represented as dictionary with possible basic values
        (dict, list, tuple, int, float, str, bool). On the beggining theese
        fields are populated and after message processing it is saved to
        database."""

        super().__init__()

        self.order = (-100, 100)

        if inmemory:
            self.client = None
            self.database = None

            self.users = {}
            self.chats = {}

        else:
            self.client = motor.motor_asyncio.AsyncIOMotorClient(host, port)
            self.database = self.client[database]

            self.users = self.database["users"]
            self.chats = self.database["chats"]

        self.inmemory = inmemory

    async def _save(self, xid, d, x):
        if isinstance(xid, str):
            xid = int(xid)

        if xid == 0:
            return None

        if "id" not in d:
            d["id"] = xid

        if self.inmemory:
            x[xid] = d
            return True

        if "_id" not in d:
            return await x.insert_one(d)

        return await x.replace_one({"_id": {"$eq": d["_id"]}}, d)

    async def save_user(self, user_id, data):
        return await self._save(user_id, data, self.users)

    async def save_chat(self, chat_id, data):
        return await self._save(chat_id, data, self.chats)

    async def _load(self, xid, x):
        if isinstance(xid, str):
            xid = int(xid)

        if xid == 0:
            return None

        if self.inmemory:
            return x.get(xid) or {"id": xid, "created": time.time()}

        return await x.find_one({"id": {"$eq": xid}}) or \
            {"id": xid, "created": time.time()}

    async def load_user(self, user_id):
        return await self._load(user_id, self.users)

    async def load_chat(self, chat_id):
        return await self._load(chat_id, self.chats)

    async def global_before_message_checks(self, msg):
        if not self.inmemory:
            msg.meta["mongodb_client"] = self.client

        msg.meta["data_user"] = await self.load_user(msg.user_id)
        msg.meta["data_chat"] = await self.load_chat(msg.chat_id) if \
            msg.is_multichat else None

    async def global_before_event_checks(self, evnt):
        if not self.inmemory:
            evnt.meta["mongodb_client"] = self.client

        if hasattr(evnt, "user_id"):
            evnt.meta["data_user"] = await self.load_user(evnt.user_id)
        else:
            evnt.meta["data_user"] = None

        if hasattr(evnt, "chat_id"):
            evnt.meta["data_chat"] = await self.load_chat(evnt.chat_id)
        else:
            evnt.meta["data_chat"] = None

    async def global_after_message_process(self, msg, res):
        if msg.meta["data_user"]:
            await self.save_user(msg.user_id, msg.meta["data_user"])

        if msg.meta["data_chat"]:
            await self.save_chat(msg.chat_id, msg.meta["data_chat"])

    async def globa_after_event_process(self, evnt, res):
        if evnt.meta["data_user"] and hasattr(evnt, "user_id"):
            await self.save_user(evnt.user_id, evnt.meta["data_user"])

        if evnt.meta["data_chat"] and hasattr(evnt, "chat_id"):
            await self.save_chat(evnt.chat_id, evnt.meta["data_chat"])
