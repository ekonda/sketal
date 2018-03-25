from handler.base_plugin_command import CommandPlugin

import aiohttp

from random import choice

from vk.data import Message

import xmltodict


class YandexNewsPlugin(CommandPlugin):
    __slots__ = ("error", "main_commands", "help_words")

    news = {"армия": "https://news.yandex.ru/army.rss",
            "авто": "https://news.yandex.ru/auto.rss",
            "мир": "https://news.yandex.ru/world.rss",
            "главное": "https://news.yandex.ru/index.rss",
            "игры": "https://news.yandex.ru/games.rss",
            "интеренет": "https://news.yandex.ru/internet.rss",
            "кино": "https://news.yandex.ru/movies.rss",
            "музыка": "https://news.yandex.ru/music.rss",
            "политика": "https://news.yandex.ru/politics.rss",
            "наука": "https://news.yandex.ru/science.rss",
            "экономика": "https://news.yandex.ru/business.rss",
            "спорт": "https://news.yandex.ru/sport.rss",
            "происшествия": "https://news.yandex.ru/incident.rss",
            "космос": "https://news.yandex.ru/cosmos.rss"}

    def __init__(self, main_commands=None, help_words=None, prefixes=None,
                 strict=False, error="Произошла ошибка! Попробуйте позже."):
        """Answers with a news from News.Yandex."""

        if main_commands is None:
            main_commands = ["новости"]

        super().__init__(*main_commands, prefixes=prefixes, strict=strict)

        self.main_commands = main_commands
        self.help_words = help_words if help_words else ["помощь", "help", "темы"]

        self.error = error

        self.set_description()

    def set_description(self):
        p = self.prefixes[-1] if self.prefixes else ""
        self.description = [f"Новости",
                            f"Показать новости.",
                            f"{p}{self.main_commands[0]} - показать новость.",
                            f"{p}{self.main_commands[0]} [тема] - показать случайную новость.",
                            f"{p}{self.main_commands[0]} {self.help_words[0]} - показать доступные темы."]

    async def process_message(self, msg: Message):
        command, text = self.parse_message(msg)

        if text.lower() in self.help_words:
            return await msg.answer("Помощь:\n" + "\n".join(self.description) + "\n\nДоступные темы:\n" +
                                    ', '.join([k.capitalize() for k in self.news.keys()]))

        url = self.news["главное"]
        if text.lower() in self.news:
            url = self.news[text]

        async with aiohttp.ClientSession() as sess:
            async with sess.get(url) as resp:
                xml = xmltodict.parse(await resp.text())

                if "rss" not in xml or "channel" not in xml["rss"] or "item" not in xml["rss"]["channel"]:
                    return await msg.answer(self.error)

                items = xml["rss"]["channel"]["item"]
                item = choice(items)

                if "title" not in item or "description" not in item:
                    return await msg.answer(self.error)

                return await msg.answer(f'👉 {item["title"]}\n'
                                        f'👉 {item["description"]}')
