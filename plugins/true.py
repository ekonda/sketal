# -*- coding: utf-8 -*-

import random


class Plugin:
    vk = None

    def __init__(self, vk):
        self.vk = vk
        print('Правда')

    def getkeys(self):
        keys = [u'правда', 'предсказание', u'true', u'реши', u'шар']
        ret = {}
        for key in keys:
            ret[key] = self
        return ret

    def call(self, msg):
        answers = []

        answers.append(u'Я думаю, что это хороший план.')
        answers.append(u'Да')
        answers.append(u'Нет')
        answers.append(u'Скорее да, чем нет.')
        answers.append(u'Не уверен...')
        answers.append(u'Однозначно нет!')
        answers.append(u'Если ты не фанат аниме, у тебя все получится!')
        answers.append(u'Возможно.')
        answers.append(u'Не могу дать точный ответ.')

        self.vk.respond(msg, {'message': random.choice(answers)})
