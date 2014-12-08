# -*- coding: utf-8 -*-

import random


class Plugin:
    vk = None

    def __init__(self, vk):
        self.vk = vk
        print('Плагин музыки')

    def getkeys(self):
        keys = [u'музыка', u'музыку', 'music']
        ret = {}
        for key in keys:
            ret[key] = self
        return ret

    def call(self, msg):
        music = None

        errors = []
        errors.append(u'Открой аудио, мудак!')
        errors.append(u'Мудак, аудиозаписи открой!')
        errors.append(u'Я бы с радостью тебе дал музыки, но ты мудак')

        try:
            count = self.vk.api.method('audio.getRecommendations',
                {'user_id': msg['user_id'], 'count': 1})

            music = self.vk.api.method('audio.getRecommendations',
                {'user_id': msg['user_id'],
                'offset': random.randint(0, count['count'] - 5),
                'count': 5})
        except:
            self.vk.respond(msg, {'message': random.choice(errors)})

        musicatt = []

        for attach in music['items']:
            user = attach['owner_id']
            ident = attach['id']
            musicatt.append('audio' + str(user) + '_' + str(ident))

        answers = []
        answers.append(u'Вот твоя музыка')
        answers.append(u'Музыку заказывали?')
        answers.append(u'Бесплатная музыка!')

        attstring = ''

        for item in musicatt:
            attstring += item + ','

        if attstring == '':
            self.vk.respond(msg, {'message': random.choice(errors)})
        else:
            self.vk.respond(msg, {'message': random.choice(answers),
            'attachment': attstring})
