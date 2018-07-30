from handler.base_plugin import CommandPlugin
from utils import EventType, parse_user_id

import time


class ChatKickerPlugin(CommandPlugin):
    __slots__ = ("admins", "exiled", "admins_only", "unkick")

    def __init__(self, commands=None, free_commands=None, prefixes=None,
            strict=False, admins_only=True):
        """Allows admins to kick users for short amount of time.
        [prefix][command] [time in seconds if kicking]"""

        if not free_commands:
            free_commands = ("освободить", "анкик", "приг")

        if not commands:
            commands = ("кик", "удалить")

        super().__init__(*(commands + free_commands), prefixes=prefixes, strict=strict)

        self.admins_only = admins_only
        self.unkick = free_commands
        self.exiled = {}

    async def process_message(self, msg):
        if not msg.is_multichat:
            return await msg.answer("🤜🏻 Это не беседа.")

        if self.admins_only and not msg.meta["is_admin_or_moder"]:
            return await msg.answer("🤜🏻 У вас недостаточно прав.")

        command, text = self.parse_message(msg)

        if command in self.unkick:
            inv = True
        else:
            inv = False

        parts = text.split(" ")
        kick_time = 300
        puid = None

        puid = await parse_user_id(msg)

        if len(parts) > 0 and parts[0].isdigit():
            if puid is not None:
                kick_time = int(parts[0])

            else:
                puid = int(parts[0])

        if not puid:
            return await msg.answer(f"Введите ID пользователя, которого хотите "
                                    f"{'вернуть или добавить' if inv else 'выкинуть'}.")

        if inv:
            if puid in self.exiled:
                del self.exiled[puid]

            return await self.api.messages.addChatUser(chat_id=msg.chat_id, user_id=puid)

        if len(parts) > 1 and " ".join(parts[1:]).isdigit():
            kick_time = int(" ".join(parts[1:]))

        self.exiled[puid] = time.time() + kick_time

        await self.api.messages.removeChatUser(chat_id=msg.chat_id, user_id=puid)

    async def check_event(self, evnt):
        return evnt.type == EventType.ChatChange

    async def process_event(self, evnt):
        if evnt.source_act == "chat_invite_user" and evnt.source_mid in self.exiled:
            dtime = self.exiled[evnt.source_mid] - time.time()

            if dtime > 0:
                await self.bot.api.messages.send(chat_id=evnt.chat_id, message=f"Вы сможете вернуться в чат "
                                                                               f"через {int(dtime)} секунд(у/ы)")

                return await self.api.messages.removeChatUser(chat_id=evnt.chat_id, user_id=evnt.source_mid)

            del self.exiled[evnt.source_mid]

        return False
