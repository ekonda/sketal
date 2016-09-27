# -*- coding: utf-8 -*-

import random
from plugin_system import Plugin

plugin = Plugin('Правда')

# Инициализируем возможные ответы
answers = []
answers.append('Абсолютно точно!')
answers.append('Да.')
answers.append('Нет.')
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


@plugin.on_command('правда', 'предсказание', 'реши', 'шар')
def call(vk, msg, args):
    vk.respond(msg, {'message': "🎱" + random.choice(answers)})

@plugin.on_command('админ')
def call(vk, msg, args):
    vk.respond(msg, {'message' : "Нет, ты не админ! Админ - vk.com/id170831732!"})