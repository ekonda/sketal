from handler.base_plugin import BasePlugin


class UserMetaPlugin(BasePlugin):
    __slots__ = ("users",)

    def __init__(self):
        """Adds `user_info` to messages and events's meta with user's data
        if available (https://vk.com/dev/users.get). You can refresh data
        with coroutine stored in `meta['user_info_refresh']`."""
        super().__init__()

        self.order = (-91, 91)

        self.users = {}

    async def update_user_info(self, user_id, refresh=False):
        if user_id == 0 :
            return False

        current_data = self.users.get(user_id)

        if not refresh and current_data:
            return current_data

        new_data = await self.api.users.get(user_ids=user_id,
            fields="sex,screen_name,nickname") or {}

        if not new_data:
            return None

        if len(self.users) > 50000:
            from random import random
            self.users = dict((k, v) for k, v in self.users.items() if random() > 0.25)

        self.users[user_id] = new_data[0]

        return self.users[user_id]

    def create_refresh(self, user_id):
        async def func():
            return await self.update_user_info(user_id, True)

        return func

    async def global_before_message_checks(self, msg):
        info = await self.update_user_info(msg.user_id)

        if info:
            msg.meta["user_info_refresh"] = self.create_refresh(msg.user_id)
            msg.meta["user_info"] = {"raw": info}

    async def global_before_event_checks(self, evnt):
        if not hasattr(evnt, "user_id"):
            return

        info = await self.update_user_info(evnt.user_id)

        if info:
            evnt.meta["user_info_refresh"] = self.create_refresh(evnt.user_id)
            evnt.meta["user_info"] = {"raw": info}
