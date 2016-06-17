# -*- coding: utf-8 -*-

import random
import requests

class Plugin:
    vk = None
	
    plugin_type = 'command'

    def __init__(self, vk):
        self.vk = vk
        print('Шутки')

    def getkeys(self):
        keys = [u'пошути', u'&рассмеши', u'петросян', u'joke']
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
        answers.append(u'Ахахахахха, вот я реально ржу!!!')
        answers.append(u'&#127770;')
        answers.append(u'Ща смешно будет, отвечаю!')
        answers.append(u'Шуточки заказывали?')
        answers.append(u'Петросян в душе прям бушует &#127770;')
		
        try:
            joke = r.json()[0]['content']
        except:
            self.vk.respond(msg, {'message': u'У меня шутилка сломалась &#127770;'})
		
        self.vk.respond(msg, {'message': random.choice(answers) + '\n' + unicode(joke)})
