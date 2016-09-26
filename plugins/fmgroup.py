# -*- coding: utf-8 -*-

import random


class Plugin:
    vk = None

    plugin_type = 'command'

    def __init__(self, vk):
        self.vk = vk
        print('Файнмайн записи')

    def getkeys(self):
        keys = [u'файнмайн', u'finemine']
        ret = {}
        for key in keys:
            ret[key] = self
        return ret

    def call(self, msg):
        answers = []
        answers.append(u"Куйня какая-то!")
        answers.append(u"Великолепно (Нет)")
        answers.append(u"Я сам смотреть не буду, но вы смотрите.")

        isphoto = False
        boobs = None

        while isphoto is False:
            values = {
                # owner_id = ид группы
                'owner_id': -35140461,
                'offset': random.randint(1, 1000),
                'count': 1
            }

            boobs = self.vk.method('wall.get', values)
            if 'attachments' in boobs['items'][0]:
                if 'photo' in boobs['items'][0]['attachments'][0]:
                    isphoto = True

        boobs_att = boobs['items'][0]['attachments'][0]['photo']

        owner_id = str(boobs_att['owner_id'])
        att_id = str(boobs_att['id'])
        access_key = str(boobs_att['access_key'])

        attachment = 'photo' + owner_id + '_' + att_id + '_' + access_key

        print attachment

        self.vk.respond(msg, {'message': random.choice(answers),
                              'attachment': attachment})
