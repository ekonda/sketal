import random

from handler.base_plugin_command import CommandPlugin


class MembersPlugin(CommandPlugin):
    __slots__ = ("show_offline", "emojis")

    def __init__(self, *commands, prefixes=None, strict=False, show_offline=False):
        """Answers with users in conference. Doesn't show users offline if `show_offline` is False."""

        super().__init__(*commands, prefixes=prefixes, strict=strict)

        self.show_offline = show_offline

        self.emojis = ['😏', '😄', '😠', '😆', '🤐', '😝', '🤔', '😎', '😐', '🙁',
                       '😨', '🤔', '😠', '😝', '😘', '😗', '😙', '😙', '😟']

        self.set_description()

    def set_description(self):
        example = self.command_example()
        self.description = [f"Состав беседы",
                            f"Вывод списка пользователей в конференции.",
                            f"{example} - показать список."]

    async def process_message(self, msg):
        if msg.is_multichat:
            all_users = await msg.api.messages.getChatUsers(chat_id=msg.chat_id, fields='name,online')

            users = ""

            for user in all_users:
                random.seed(user['id'])

                emoji = random.choice(self.emojis) + " "

                if self.show_offline:
                    users += f"{emoji} [id{user['id']}|{user['first_name']} {user['last_name']}] " \
                             f"{' - онлайн' if user['online'] else ''}\n"

                elif user['online']:
                    users += f"{emoji} [id{user['id']}|{user['first_name']} {user['last_name']}]\n"

            if self.show_offline:
                await msg.answer(f'👽 Состав беседы:\n' + users)

            else:
                await msg.answer(f'👽 Сейчас в беседе:\n' + users)

        else:
            await msg.answer("Эту команду можно использовать только в беседе.")
