# -*- coding: utf-8 -*-

import random


class Plugin:
    vk = None

    plugin_type = 'command'

    def __init__(self, vk):
        self.vk = vk
        print('Правда')

    def getkeys(self):
        keys = [u'правда', u'предсказание', u'true', u'реши', u'шар']
        ret = {}
        for key in keys:
            ret[key] = self
        return ret

    def call(self, msg):
        answers = []

        answers.append(u'Абсолютно точно!')
        answers.append(u'Да')
        answers.append(u'Нет')
        answers.append(u'Скорее да, чем нет.')
        answers.append(u'Не уверен...')
        answers.append(u'Однозначно нет!')
        answers.append(u'Если ты не фанат аниме, у тебя все получится!')
        answers.append(u'Можешь быть уверен в этом.')
        answers.append(u'Перспективы не очень хорошие.')
        answers.append(u'А как же иначе?.')
        answers.append(u'Да, но если только ты не смотришь аниме.')
        answers.append(u'Знаки говорят — «да».')
        answers.append(u'Не знаю.')
        answers.append(u'Мой ответ — «нет».')
        answers.append(u'Весьма сомнительно.')
        answers.append(u'Не могу дать точный ответ.')

        self.vk.respond(msg, {'message': random.choice(answers)})
