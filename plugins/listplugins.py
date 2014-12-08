# -*- coding: utf-8 -*-

import os
import sys


class Plugin:
    vk = None

    def __init__(self, vk):
        self.vk = vk
        print('Список плагинов')

    def getkeys(self):
        keys = [u'плагины', 'plugins']
        ret = {}
        for key in keys:
            ret[key] = self
        return ret

    def call(self, msg):
        lists = ''
        path = 'plugins/'
        sys.path.insert(0, path)
        for f in os.listdir(path):
            fname, ext = os.path.splitext(f)
            if ext == '.py':
                lists += fname + ' '
        sys.path.pop(0)
        self.vk.respond(msg, {'message': u'Загруженные плагины:\n' + lists})