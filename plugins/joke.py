import random
import requests
from plugin_system import Plugin

plugin = Plugin('Шутки')

answers = []
answers.append('Ахахахахха, вот я реально ржу!!!')
answers.append('&#127770;')
answers.append('Ща смешно будет, отвечаю!')
answers.append('Шуточки заказывали?')
answers.append('Петросян в душе прям бушует &#127770;')


@plugin.on_command('шутка', 'пошути', 'рассмеши', 'петросян')
def joke_get(vk, msg, args):
    resp = requests.get('http://www.umori.li/api/get?site=bash.im&name=bash&num=1')
    try:
        joke = resp.json()[0]['elementPureHtml']
    except:
        vk.respond(msg, {'message': 'У меня шутилка сломалась &#127770;'})
        return

    vk.respond(msg, {'message': random.choice(answers) + '\n' + str(joke)})
