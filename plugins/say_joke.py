import random
import requests
from plugin_system import Plugin

plugin = Plugin('Шутки')

answers = '''А вот и шуточки подъехали!!!
Сейчас будет смешно, зуб даю!
Шуточки заказывали?
Петросян в душе прям бушует :)
'''.splitlines()


@plugin.on_command('шутка', 'пошути', 'рассмеши', 'петросян', 'расскажи шутку')
async def joke_get(msg, args):
    resp = requests.post('http://randstuff.ru/joke/generate/')
    try:
        joke = resp.json()['joke']['text']
    except:
        return await msg.answer("У меня шутилка сломалась :(")

    await msg.answer(random.choice(answers) + '\n' + str(joke))
