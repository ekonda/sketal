# -*- coding: utf-8 -*-

import random


class Plugin:
    vk = None

    plugin_type = 'command'

    def __init__(self, vk):
        self.vk = vk
        print('Правда')

    def getkeys(self):
        keys = ['правда', 'предсказание', 'true', 'реши', 'шар']
        ret = {}
        for key in keys:
            ret[key] = self
        return ret

    def call(self, msg):
        answers = []

        answers.append('Абсолютно точно!')
        answers.append('Да')
        answers.append('Нет')
        answers.append('Скорее да, чем нет.')
        answers.append('Не уверен...')
        answers.append('Однозначно нет!')
        answers.append('Если ты не фанат аниме, у тебя все получится!')
        answers.append('Можешь быть уверен в этом.')
        answers.append('Перспективы не очень хорошие.')
        answers.append('А как же иначе?.')
        answers.append('Да, но если только ты не смотришь аниме.')
        answers.append('Знаки говорят — «да».')
        answers.append('Не знаю.')
        answers.append('Мой ответ — «нет».')
        answers.append('Весьма сомнительно.')
        answers.append('Не могу дать точный ответ.')

        self.vk.respond(msg, {'message': random.choice(answers)})
