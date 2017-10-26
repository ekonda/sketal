import random

from handler.base_plugin_command import CommandPlugin


class PairPlugin(CommandPlugin):
    __slots__ = ("text", )

    def __init__(self, *commands, prefixes=None, strict=False, text="❤ Любит ❤ "):
        """Answers with 2 users separated by text `text` defaults to "❤ Любит ❤ "."""

        super().__init__(*commands, prefixes=prefixes, strict=strict)

        self.text = text

        self.set_description()

    def set_description(self):
        example = self.command_example()
        self.description = [f"Кто кого",
                            f"Узнайте, кто кого любит ;)",
                            f"{example} - всё тайное станет явным."]

    async def process_message(self, msg):
        if msg.is_multichat:
            users = await msg.api.messages.getChatUsers(chat_id=msg.chat_id, fields='name')
            love1, love2 = random.sample(users, 2)
            await msg.answer(f"[id{love1['id']}|{love1['first_name']} {love1['last_name']}] - {self.text} - "
                             f"[id{love2['id']}|{love2['first_name']} {love2['last_name']}]")

        else:
            await msg.answer("Эту команду можно использовать только в беседе.")
