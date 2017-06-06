import random

import aiohttp

from plugin_system import Plugin

plugin = Plugin('Шутки',
                usage='пошути - написать случайный анекдот')

answers = '''А вот и шуточки подъехали!!!
Сейчас будет смешно, зуб даю!
Шуточки заказывали?
Петросян в душе прям бушует :)
'''.splitlines()

URL = "http://rzhunemogu.ru/RandJSON.aspx?CType=1"


@plugin.on_command('шутка', 'пошути', 'рассмеши')
async def joke_get(msg, args):
    async with aiohttp.ClientSession() as sess:
        async with sess.get(URL) as resp:
            text = await resp.text()
            joke = "".join(text.replace('\r\n', '\n').split("\"")[3:-1])
    await msg.answer(random.choice(answers) + '\n' + str(joke))
