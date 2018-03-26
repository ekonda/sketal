from handler.base_plugin import BasePlugin

import time

import motor.motor_asyncio


class StoragePlugin(BasePlugin):
    __slots__ = ("client", "database", "users", "chats")

    def __init__(self, host="localhost", port=27017, database="sketal_db"):
        """Allows users and chats to store persistent data. Both storages are
        siuated in `meta` as `data_user` and `data_chat` and represented as
        dictionary with possible basic values (dict, list, tuple, int, float,
        str, bool). On the beggining theese fields are populated and after
        message processing it is saved to database."""

        super().__init__()
        self.order = (-100, 100)

        self.client = motor.motor_asyncio.AsyncIOMotorClient(host, port)

        self.database = self.client[database]

        self.users = self.database["users"]
        self.chats = self.database["chats"]

    async def _save(self, xid, d, x):
        if isinstance(xid, str):
            xid = int(xid)

        if "_id" not in d:
            if "id" not in d:
                d["id"] = xid

            return await x.insert_one(d)

        return await x.update_one({"_id": d["_id"]}, d)

    async def save_user(self, user_id, data):
        return await self._save(user_id, data, self.users)

    async def save_chat(self, chat_id, data):
        return await self._save(chat_id, data, self.chats)

    async def _load(self, xid, x):
        if isinstance(xid, str):
            xid = int(xid)

        return await x.find_one({"id": {"$eq": xid}}) or \
            {"id": xid, "created": time.time()}

    async def load_user(self, user_id):
        return await self._load(user_id, self.users)

    async def load_chat(self, chat_id):
        return await self._load(chat_id, self.chats)

    async def global_before_message_checks(self, msg):
        msg.meta["data_user"] = await self.load_user(msg.user_id)
        msg.meta["data_chat"] = await self.load_chat(msg.chat_id) if \
            msg.is_multichat else None

    async def global_before_event_checks(self, evnt):
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
            if isinstance(msg.meta, dict):
                if "_id" in msg.meta["data_user"]:
                    _id = msg.meta["data_user"].pop("_id")

                    self.users.replace_one(
                        {"_id": _id},
                        msg.meta["data_user"]
                    )
                else:
                    self.users.insert_one(msg.meta["data_user"])

        if msg.meta["data_chat"]:
            if isinstance(msg.meta, dict):
                if "_id" in msg.meta["data_chat"]:
                    _id = msg.meta["data_chat"].pop("_id")

                    self.chats.replace_one(
                        {"_id": _id},
                        msg.meta["data_chat"]
                    )
                else:
                    self.chats.insert_one(msg.meta["data_chat"])

    async def globa_after_event_process(self, evnt, res):
        evnt.meta["data_user"] = self
        evnt.meta["data_chat"] = self
