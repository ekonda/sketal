# -*- coding: utf-8 -*-

import random


class Plugin:
    vk = None
	
    plugin_type = 'command'

    def __init__(self, vk):
        self.vk = vk
        print('Аниме')

    def getkeys(self):
        keys = [u'аниме', 'anime', u'анима', u'анимэ']
        ret = {}
        for key in keys:
            ret[key] = self
        return ret

    def call(self, msg):
        greetings = []

        greetings.append(u'Мамо, помоги. До мэнэ докапались анимешники!')
        greetings.append(u'Фу, иди нахуй, пидор')
        greetings.append(u'Фанат боку но пико, что-ли?')
        greetings.append(u'С пидорами не общаюсь')
        greetings.append(u'Долбитесь в зад без меня!')

        self.vk.respond(msg, {'message': random.choice(greetings)})
