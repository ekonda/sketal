import random
import requests
from plugin_system import Plugin

plugin = Plugin('Шутки')

answers = '''Ахахахахха, вот я реально ржу!!!
🌚
Ща смешно будет, отвечаю!
Шуточки заказывали?
Петросян в душе прям бушует 🌚
'''.splitlines()

@plugin.on_command('шутка', 'пошути', 'рассмеши', 'петросян', 'скажи шутку')
async def joke_get(vk, msg, args):
    resp = requests.get('http://www.umori.li/api/get?site=bash.im&name=bash&num=1')
    try:
        joke = resp.json()[0]['elementPureHtml']
    except:
        await vk.respond(msg, {'message': 'У меня шутилка сломалась &#127770;'})
        return

    await vk.respond(msg, {'message': random.choice(answers) + '\n' + str(joke)})
