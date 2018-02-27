from handler.base_plugin import BasePlugin


class ChatData:
    __slots__ = ("admin_id", "users", "id", "previous_users")

    def __init__(self, cid, admin_id, users):
        self.id = cid

        self.admin_id = admin_id
        self.users = users
        self.previous_users = []


class ChatMetaPlugin(BasePlugin):
    __slots__ = ("chats")

    def __init__(self):
        """Adds self to messages and chat's data if available.
        """

        super().__init__()

        self.chats = {}

    async def get_chat_data(self, chat_id, refresh=False):
        if chat_id == 0:
            return None

        if not refresh and chat_id in self.chats:
            return self.chats[chat_id]

        chat = await self.api.messages.getChat(chat_id=chat_id, fields="sex,screen_name,nickname")
        chat_data = ChatData(chat["id"], chat["admin_id"], chat["users"])

        if chat_id in self.chats:
            chat_data.previous_users = self.chats[chat_id].users

        self.chats[chat_id] = chat_data

        return chat_data

    def create_refresh(self, chat_id):
        async def func():
            return await self.get_chat_data(chat_id, True)

        return func

    async def global_before_message_checks(self, msg):
        msg.meta["__refresh_chat_data"] = self.create_refresh(msg.chat_id)
        msg.meta["__chat_data"] = await self.get_chat_data(msg.chat_id)

    async def global_before_event_checks(self, evnt):
        if not hasattr(evnt, "chat_id"):
            return

        evnt.meta["__refresh_chat_data"] = self.create_refresh(evnt.chat_id)
        evnt.meta["__chat_data"] = await self.get_chat_data(evnt.chat_id)

    async def process_event(self, evnt):
        if evnt.source_act in "chat_invite_user":
            await evnt.meta["__refresh_chat_data"]()
            
        return False
