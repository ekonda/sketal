# -*- coding: utf-8 -*-


class Plugin:
    vk = None

    def __init__(self, vk):
        self.vk = vk
        print('Пример плагина')

    def getkeys(self):
        keys = [u'примерплагина', u'тестовыйплагин']
        ret = {}
        for key in keys:
            ret[key] = self
        return ret

    def call(self, msg):
        self.vk.respond(msg, {'message': u'Пример плагина'})