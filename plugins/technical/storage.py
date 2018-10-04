from handler.base_plugin import BasePlugin

import json

import motor.motor_asyncio


class sdict(dict):
    """Dictionary with field `changed`. `changed` is True when any element was
    accessed."""

    def __init__(self, *args, **kwargs):
        self.changed = False
        super().__init__(*args, **kwargs)

    def __getitem__(self, item):
        self.changed = True
        return super().__getitem__(item)

    def __setitem__(self, item, value):
        self.changed = True
        return super().__setitem__(item, value)

    def __delitem__(self, item):
        self.changed = True
        super().__delitem__(item)

    def getraw(self, item, default=None):
        try:
            return super().__getitem__(item)
        except KeyError:
            return default

    def setraw(self, item, value):
        super().__setitem__(item, value)

    def delraw(self, item):
        super().__delitem__(item)


class StoragePlugin(BasePlugin):
    __slots__ = ("client", "database", "users", "chats", "meta", "cached_meta",
        "in_memory", "save_to_file")

    def __init__(self, host="localhost", port=27017, database="sketal_db",
            in_memory=False, save_to_file=False):
        """Allows users and chats to store persistent data with MongoDB or in
        memory. Both storages are situated in `meta` as `data_user` and
        `data_chat` and represented as dictionary with possible basic values
        (dict, list, tuple, int, float, str, bool). On the beggining theese
        fields are populated and after message processing it is saved to
        database.

        Data is saved only if was acessed. You can use `sdict`'s methods and
        field `changed` for accessing data without saving it."""

        super().__init__()

        self.order = (-100, 100)

        if in_memory:
            self.client = None
            self.database = None

            self.users = sdict()
            self.chats = sdict()
            self.meta = sdict()

            if save_to_file:
                path = self.get_path("storage.localdata.json")

                try:
                    with open(path) as o:
                        u, c, m = json.load(o)

                        for k, v in u.items():
                            self.users[int(k)] = v

                        for k, v in c.items():
                            self.chats[int(k)] = v

                        for k, v in m.items():
                            if isinstance(k, str) and k.isdigit():
                                print("Storage :: You use number in "
                                    "string format in storage with `in_memory`."
                                        " It can be a mistake.")

                            self.meta[k] = v

                except ValueError:
                    import traceback
                    traceback.print_exc()

                    print("Storage :: File `" + path + "` is broken.")

                except FileNotFoundError:
                    pass

        else:
            if save_to_file:
                raise AttributeError("You can't use `save_to_file` with "
                    "`in_memory` equals to False")

            self.client = motor.motor_asyncio.AsyncIOMotorClient(host, port)

            self.database = self.client[database]

            self.users = self.database["users"]
            self.chats = self.database["chats"]
            self.meta = self.database["meta"]

        self.cached_meta = None

        self.in_memory = in_memory
        self.save_to_file = save_to_file

    def my_path(self):
        return self.get_path("admin_lists.localdata.json")

    async def stop(self):
        if not self.save_to_file:
            return

        target = (self.users, self.chats, self.meta)

        if not target:
            return

        with open(self.get_path("storage.localdata.json"), "w") as o:
            json.dump(target, o)

    async def _save(self, xid, d, x):
        if isinstance(xid, str):
            xid = int(xid)

        if xid == 0 or not d or not d.changed:
            return None

        if "id" not in d:
            d["id"] = xid

        if self.in_memory:
            cur = x.get(xid)

            if not cur or cur["_version"] == d["_version"]:
                d["_version"] += 1
                x[xid] = d
                return True

            return False

        if "_id" not in d:
            return await x.insert_one(d)

        old_ver = d["_version"]
        d["_version"] += 1

        res = await x.replace_one({"_id": {"$eq": d["_id"]},
            "_version": {"$eq": old_ver}}, d)

        if res.modified_count == 0:
            return False

        return True

    async def save_user(self, user_id, data):
        return await self._save(user_id, data, self.users)

    async def save_chat(self, chat_id, data):
        return await self._save(chat_id, data, self.chats)

    async def _load(self, xid, x):
        if isinstance(xid, str):
            xid = int(xid)

        if xid == 0:
            return None

        if self.in_memory:
            return sdict(x.get(xid) or {"id": xid, "_version": 0})

        return sdict(await x.find_one({"id": {"$eq": xid}}) or
            {"id": xid, "_version": 0})

    async def load_user(self, user_id):
        return await self._load(user_id, self.users)

    async def load_chat(self, chat_id):
        return await self._load(chat_id, self.chats)

    async def load_meta(self, segment="main"):
        if self.cached_meta:
            self.cached_meta.changed = False
            return self.cached_meta

        if self.in_memory:
            self.cached_meta = sdict(self.meta.get(segment) or
                {"_name": segment, "_version": 0})

            return self.cached_meta

        self.cached_meta = sdict(await self.meta.find_one({"_name": {"$eq": segment}}) or
            {"_name": segment, "_version": 0})

        self.cached_meta.show = True

        return self.cached_meta

    async def save_meta(self, d, segment="main"):
        if not d or not d.changed:
            return

        self.cached_meta = None

        if self.in_memory:
            cur = self.meta.get(segment)

            if not cur or cur["_version"] == d["_version"]:
                d["_version"] += 1
                self.meta[segment] = d

                return True

            return False

        if "_id" not in d:
            return await self.meta.insert_one(d)

        old_ver = d["_version"]
        d["_version"] += 1

        res = await self.meta.replace_one({"_name": {"$eq": segment},
            "_version": {"$eq": old_ver}}, d)

        if res.modified_count == 0:
            return False

        return True

    def prepare_ctrl(self, entity):
        async def _1l():
            return await self.load_meta()
        async def _1s(d):
            return await self.save_meta(d)

        if hasattr(entity, "chat_id"):
            async def _2l():
                return await self.load_chat(entity.chat_id)

            async def _2s(d):
                return await self.save_chat(entity.chat_id, d)
        else:
            _2l = None
            _2s = None

        if hasattr(entity, "user_id"):
            async def _3l():
                return await self.load_user(entity.user_id)

            async def _3s(d):
                return await self.save_user(entity.user_id, d)
        else:
            _3l = None
            _3s = None

        return {
            "load_meta": _1l,
            "save_meta": _1s,
            "load_chat": _2l,
            "save_chat": _2s,
            "load_user": _3l,
            "save_user": _3s
        }

    async def global_before_message_checks(self, msg):
        if not self.in_memory:
            msg.meta["mongodb_client"] = self.client

        msg.meta["data_ctrl"] = self.prepare_ctrl(msg)

        msg.meta["data_meta"] = await self.load_meta()
        msg.meta["data_user"] = await self.load_user(msg.user_id)
        msg.meta["data_chat"] = await self.load_chat(msg.chat_id) if \
            msg.is_multichat else None

    async def global_before_event_checks(self, evnt):
        if not self.in_memory:
            evnt.meta["mongodb_client"] = self.client

        evnt.meta["data_ctrl"] = self.prepare_ctrl(evnt)

        if hasattr(evnt, "user_id"):
            evnt.meta["data_user"] = await self.load_user(evnt.user_id)
        else:
            evnt.meta["data_user"] = None

        if hasattr(evnt, "chat_id"):
            evnt.meta["data_chat"] = await self.load_chat(evnt.chat_id)
        else:
            evnt.meta["data_chat"] = None

    async def save_target_meta(self, entity):
        ctrl = entity.meta["data_ctrl"]

        if ctrl["save_meta"]:
            await ctrl["save_meta"](entity.meta["data_meta"])

        if ctrl["save_user"]:
            await ctrl["save_user"](entity.meta["data_user"])

        if ctrl["save_chat"] and entity.meta["data_chat"]:
            await ctrl["save_chat"](entity.meta["data_chat"])

    async def global_after_message_process(self, msg, result):
        await self.save_target_meta(msg)

    async def globa_after_event_process(self, evnt, res):
        await self.save_target_meta(evnt)
