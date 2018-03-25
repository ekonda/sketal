import datetime

from handler.base_plugin_command import CommandPlugin
from utils import plural_form, age


class BirthdayPlugin(CommandPlugin):
    __slots__ = ("max_users_in_group", )

    def __init__(self, *commands, prefixes=None, strict=False, max_users_in_group=1000):
        """Answers with birthday for users in group (but no more than `max_users_in_group`), for users in conference."""

        super().__init__(*commands, prefixes=prefixes, strict=strict)

        self.max_users_in_group = max_users_in_group

        self.set_description()

    def set_description(self):
        example = self.command_example()
        self.description = [f"Дни рождения",
                            f"Вывод дней рождений людей в группе или в беседе.",
                            f"{example} - показать дни кождения в конференции.",
                            f"{example} <id группы> - показать дни рождения пользователей в группу."]

    async def process_message(self, msg):
        command, argument = self.parse_message(msg)

        if argument:
            members = []

            offset = 0

            while True:
                result = await msg.api.groups.getMembers(group_id=argument, offset=offset, fields="bdate")

                if not result or "items" not in result or not result["items"]:
                    if offset == 0:
                        return await msg.answer("Не удалось получить сообщество или оно пусто!")

                    break

                members += result["items"]

                offset += 1000

                if result["count"] > self.max_users_in_group:
                    await msg.answer(f"Вы пытаетесь узнать дни рождения слишком многих людей!\n"
                                     f"Будут показана лишь {self.max_users_in_group} из пользователей")

                break

            message = f"Дни рождения пользователей в группе \"{argument}\" ✨:\n"

        else:
            if not msg.is_multichat:
                members = await msg.api.users.get(user_ids=msg.user_id, fields="bdate")

                message = f"Ваш день рождения ✨:\n"

            else:
                members = await msg.api.messages.getChatUsers(chat_id=msg.chat_id, fields="bdate")

                message = f"Дни рождения пользователей в беседе ✨:\n"

        data = []

        now = datetime.datetime.today().date()

        for m in members:
            if "bdate" not in m or "deactivated" in m:
                continue

            try:
                if m['bdate'].count(".") > 1:
                    year = True
                    user_date = datetime.datetime.strptime(m['bdate'], '%d.%m.%Y').date()

                else:
                    year = False
                    user_date = datetime.datetime.strptime(m['bdate'], '%d.%m').date()

            except ValueError:
                continue

            try:
                check_date = user_date.replace(year=now.year)

            except ValueError:
                check_date = user_date + (datetime.date(now.year, 1, 1) - datetime.date(user_date.year, 1, 1))

            difference = check_date - now

            if difference.days < 0:
                check_date = check_date.replace(year=now.year + 1)

                difference = check_date - now

            bdate_in = " (будет через " + plural_form(difference.days, ("день", "дня", "дней")) + ")"

            if year:
                bdate_in = bdate_in[:-1] + ", исполнится " + plural_form(age(user_date) + 1,
                                                                         ("год", "года", "лет")) + ")"

            data.append((" 🌍 " + m["first_name"] + " " + m["last_name"] + ": "
                         + user_date.strftime("%d.%m") + bdate_in,
                         difference.days))

        message += "\n".join(d[0] for d in sorted(data, key=lambda x: x[1]))

        return await msg.answer(message)
