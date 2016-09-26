# -*- coding: utf-8 -*-


class Plugin:
    vk = None

    plugin_type = 'command'

    def __init__(self, vk):
        self.vk = vk
        print('Пример плагина')

    def getkeys(self):
        keys = ['примерплагина', 'тестовыйплагин']
        ret = {}
        for key in keys:
            ret[key] = self
        return ret

    def call(self, msg):
        print("OK!")
        self.vk.respond(msg, {'message': 'Пример плагина'})
