from handler.base_plugin import CommandPlugin


class ChatControlPlugin(CommandPlugin):
    __slots__ = ("banned", "command_add", "command_remove", "command_info",
        "cached")

    def __init__(self, command_add=None, command_remove=None, command_info=None,
            banned=None, prefixes=None, strict=False):
        """Allows admins to ban chats."""

        if not command_add:
            command_add = ("беседа бан",)

        if not command_info:
            command_info = ("беседа техинфо",)

        if not command_remove:
            command_remove = ("беседа разбан",)

        self.command_add = command_add
        self.command_info = command_info
        self.command_remove = command_remove

        super().__init__(*(self.command_add + self.command_remove +
            self.command_info), prefixes=prefixes, strict=strict)

        self.order = (-88, 88)

        self.banned = banned or ()
        self.cached = []

        self.description = [
            "Администрационные команды для чатов",
            self.prefixes[-1] + self.command_info[0] + " [список] - показать информацию о беседе или недавние беседы бота.",
            self.prefixes[-1] + self.command_add[0] + " <id беседы> - заблокировать беседу с id.",
            self.prefixes[-1] + self.command_remove[0] + " <id беседы> - разблокировать беседу с id.",
        ]

    async def load(self, entity):
        """Entity is Message or Event"""

        banned = entity.meta["data_meta"].getraw("admin_lists_banned_chats")

        if banned is None:
            banned = entity.meta["data_meta"]["admin_lists_banned_chats"] = \
                list(self.banned)

        if entity.chat_id not in self.cached:
            self.cached = self.cached[-19:] + [entity.chat_id]

        return banned

    async def process_message(self, msg):
        if not msg.chat_id:
            return await msg.answer("🤜🏻 Это не беседа.")

        command, text = self.parse_message(msg)

        if not msg.meta["is_admin"]:
            return await msg.answer("🤜🏻 У вас недостаточно прав.")

        if command in self.command_info:
            if text == "список":
                chats = await self.api.messages.getChat(
                    chat_ids=",".join(str(c) for c in self.cached))

                return await msg.answer("Недавние беседы:\n" + "\n".join(
                    f"💬 Беседа #{chat['id']}: {chat['title']}."
                        for chat in chats))

            return await msg.answer(f"💬 Беседа #{msg.chat_id}.")

        if command in self.command_add:
            ptext = text.replace("#", "", 1)

            if not ptext.isdigit():
                return await msg.answer("👀 Указанная беседа не найдена.")

            if msg.meta.get("data_meta"):
                msg.meta["data_meta"]["admin_lists_banned_chats"].\
                    append(int(ptext))
            else:
                self.banned.append(int(ptext))

            return await msg.answer(f"🙌 Беседа #{ptext} заблокирована!")

        if command in self.command_remove:
            ptext = text.replace("#", "", 1)

            if not ptext.isdigit():
                return await msg.answer("👀 Указанная беседа не найдена.")

            try:
                if msg.meta.get("data_meta"):
                    msg.meta["data_meta"]["admin_lists_banned_chats"].\
                        remove(int(ptext))
                else:
                    self.banned.remove(int(ptext))
            except ValueError:
                return await msg.answer(f"🤜🏻 Беседа #{ptext} не заблокирована!")

            return await msg.answer(f"🙌 Беседа #{ptext} разблокирована!")

    async def global_before_message_checks(self, msg):
        if not msg.chat_id:
            return

        if msg.meta.get("data_meta"):
            return msg.chat_id not in await self.load(msg)

        return msg.chat_id not in self.banned

    async def global_before_event_checks(self, evnt):
        if not hasattr(evnt, "chat_id") or not evnt.chat_id:
            return

        if evnt.meta.get("data_meta"):
            return evnt.chat_id not in await self.load(evnt)

        return evnt.chat_id not in self.banned
