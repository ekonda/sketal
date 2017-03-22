import random

import requests

from plugin_system import Plugin

plugin = Plugin('Шутки',
                usage='пошути - написать случайный анекдот')

answers = '''А вот и шуточки подъехали!!!
Сейчас будет смешно, зуб даю!
Шуточки заказывали?
Петросян в душе прям бушует :)
'''.splitlines()


@plugin.on_command('шутка', 'пошути', 'рассмеши')
async def joke_get(msg, args):
    resp = requests.get('http://rzhunemogu.ru/RandJSON.aspx?CType=1')
    try:
        joke = resp.json()['content']
    except:
        return await msg.answer("У меня шутилка сломалась :(")

    await msg.answer(random.choice(answers) + '\n' + str(joke))
