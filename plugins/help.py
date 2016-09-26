# -*- coding: utf-8 -*-

import random


class Plugin:
    vk = None

    plugin_type = 'command'

    def __init__(self, vk):
        self.vk = vk
        print('Помощь')

    def getkeys(self):
        keys = ['помощь', 'помоги', 'команды', 'commands', 'help', 'хелп']
        ret = {}
        for key in keys:
            ret[key] = self
        return ret

    def call(self, msg):
        commands = []

        commands.append(
            'Все доступные команды: \n мемы \n сиськи \n музыка \n шар \n пошути \n найди \n вики \n напиши \n двач \n луна \n шкуры \n время \n школьницы \n нет \n курс \n др \n файнмайн \n онлайн \n статистика \n привет \n рандом \n плагины')

        self.vk.respond(msg, {'message': commands})
