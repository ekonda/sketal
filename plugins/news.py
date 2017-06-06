from random import choice

import aiohttp
import xmltodict

from plugin_system import Plugin
from settings import PREFIXES
from utils import unquote

# yandex news
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

plugin = Plugin("Новости",
                usage=["новости - показать новость",
                       "новости [тема] - показать новость определённой тематики",
                       "новости помощь - показать доступные темы"])


@plugin.on_command('новости')
async def show_news(msg, args):
    url = news["главное"]

    if args:
        category = args.pop()

        if category.lower() in ["помощь", "помощ", "помоги", "помог"]:
            return await msg.answer(f"{PREFIXES[0]}новости [тема], где тема - это одно из следующих слов:\n"
                                    f"{', '.join([k[0].upper() + k[1:] for k in news.keys()])}")

        if category.lower() in news:
            url = news[category]

    async with aiohttp.ClientSession() as sess:
        async with sess.get(url) as resp:
            xml = xmltodict.parse(await resp.text())
            items = xml["rss"]["channel"]["item"]
            item = unquote(choice(items))

            return await msg.answer(f'👉 {item["title"]}\n'
                                    f'👉 {item["description"]}')
