# -*- coding: utf-8 -*-

import random


class Plugin:
    vk = None

    def __init__(self, vk):
        self.vk = vk
        print('Приветствия')

    def getkeys(self):
        keys = [u'приветствие', 'greeting', u'привет', u'голос', u'ку']
        ret = {}
        for key in keys:
            ret[key] = self
        return ret

    def call(self, msg):
        greetings = []

        greetings.append(u'Я - чатбот')
        greetings.append(u'Кекеке')
        greetings.append(u'Запущен и готов служить')
        greetings.append(u'У контакта ужасный флуд-контроль, %username%')
        greetings.append(u'Хуяк-хуяк и в продакшен')

        self.vk.respond(msg, {'message': random.choice(greetings)})
