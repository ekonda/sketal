import random

from handler.base_plugin_command import CommandPlugin


class WhoIsPlugin(CommandPlugin):
    __slots__ = ()

    def __init__(self, *commands, prefixes=None, strict=False):
        """Answers with a random user from conference with a title specified in command."""

        super().__init__(*commands, prefixes=prefixes, strict=strict)

        self.set_description()

    def set_description(self):
        example = self.command_example()
        self.description = [f"Кто есть кто",
                            f"Узнайте, кто есть кто ;)",
                            f"{example} <определение> - кто в конференции является обладателем определения."]

    async def process_message(self, msg):
        c, args = self.parse_message(msg)

        if not args:
            return await msg.answer(f"Используйте {self.command_example()} <текст>\n(без `<` или `>`)")

        if msg.is_multichat:
            users = await msg.api.messages.getChatUsers(chat_id=msg.chat_id, fields='name')
            user = random.choice(users)

            await msg.answer(f"Кто {args}? Я думаю, это {user['first_name']} {user['last_name']} 🙈")

        else:
            await msg.answer("Эту команду можно использовать только в беседе.")
