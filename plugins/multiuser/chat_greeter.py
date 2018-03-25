from handler.base_plugin import BasePlugin
from vk.utils import EventType


class ChatGreeterPlugin(BasePlugin):
    __slots__ = ("motd", )

    def __init__(self, motd="Добро пожаловать ;)!"):
        """Answers with message `motd` when user joins a chat."""

        super().__init__()

        self.motd = motd

    async def check_message(self, msg):
        return False

    async def check_event(self, evnt):
        return evnt.type == EventType.ChatChange

    async def process_event(self, evnt):
        if evnt.source_act == "chat_invite_user":
            return await self.bot.api.messages.send(chat_id=evnt.chat_id, message=self.motd)

        return False
