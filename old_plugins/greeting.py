# -*- coding: utf-8 -*-

import random


class Plugin:
    vk = None

    plugin_type = 'command'

    def __init__(self, vk):
        self.vk = vk
        print('Приветствия')

    def getkeys(self):
        keys = ['приветствие', 'greeting', 'привет', 'голос', 'ку']
        ret = {}
        for key in keys:
            ret[key] = self
        return ret

    def call(self, msg):
        greetings = []

        greetings.append('Слава Украине!')
        greetings.append('Кекеке')
        greetings.append('Запущен и готов служить!')
        greetings.append('У контакта ужасный флуд-контроль, %username%')
        greetings.append('Хуяк-хуяк и в продакшен')

        self.vk.respond(msg, {'message': random.choice(greetings)})
