
import random
import requests


class Plugin:
    vk = None

    plugin_type = 'command'

    def __init__(self, vk):
        self.vk = vk
        print('Шутки')

    def getkeys(self):
        keys = ['пошути', 'рассмеши', 'петросян', 'joke']
        ret = {}
        for key in keys:
            ret[key] = self
        return ret

    def call(self, msg):
        pars = {
            'format': 'json',
            'type': 'random',
            'amount': '1',
        }
        r = requests.get('http://shortiki.com/export/api.php', params=pars)

        answers = []
        answers.append('Ахахахахха, вот я реально ржу!!!')
        answers.append('&#127770;')
        answers.append('Ща смешно будет, отвечаю!')
        answers.append('Шуточки заказывали?')
        answers.append('Петросян в душе прям бушует &#127770;')

        try:
            joke = r.json()[0]['content']
        except:
            self.vk.respond(msg, {'message': 'У меня шутилка сломалась &#127770;'})

        self.vk.respond(msg, {'message': random.choice(answers) + '\n' + str(joke)})
