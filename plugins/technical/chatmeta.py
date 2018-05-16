from handler.base_plugin import BasePlugin


class ChatMetaPlugin(BasePlugin):
    __slots__ = ("chats",)

    def __init__(self):
        """Adds `chat_info` to messages and events's meta["data_chat"] with
        chat's data if available (https://vk.com/dev/messages.getChat). You can
        refresh data with coroutine stored in `meta['chat_info_refresh']`."""
        super().__init__()

        self.order = (-90, 90)

        self.chats = {}

    async def update_chat_info(self, entity, refresh=False):
        """Argument `entity` must be Message or Event"""

        if entity.chat_id == 0 or not entity.meta.get("data_chat"):
            return False

        current_data = entity.meta["data_chat"].get("chat_info")

        if not refresh and current_data:
            return True

        new_data = await self.api.messages.getChat(chat_id=entity.chat_id,
            fields="sex,screen_name,nickname") or {}

        if current_data:
            new_data["prev_users"] = current_data["users"]
        else:
            new_data["prev_users"] = []

        entity.meta["data_chat"]["chat_info"] = new_data

        return True

    def create_refresh(self, entity):
        """Argument `entity` must be Message or Event"""

        async def func():
            return await self.update_chat_info(entity, True)

        return func

    async def global_before_message_checks(self, msg):
        if await self.update_chat_info(msg):
            msg.meta["chat_info_refresh"] = self.create_refresh(msg)

    async def global_before_event_checks(self, evnt):
        if not hasattr(evnt, "chat_id"):
            return

        if await self.update_chat_info(evnt):
            evnt.meta["chat_info_refresh"] = self.create_refresh(evnt)

    async def process_event(self, evnt):
        if evnt.source_act in "chat_invite_user" and \
                evnt.meta["data_chat"].get("chat_info"):
            await evnt.meta["chat_info_refresh"]()

        return False
