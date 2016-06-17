# -*- coding: utf-8 -*-

import random


class Plugin:
    vk = None
	
    plugin_type = 'command'

    def __init__(self, vk):
        self.vk = vk
        print('Счетчики')

    def getkeys(self):
        keys = [u'счетчики', u'счетчик', u'count', u'статистика', u'стата', u'stats']
        ret = {}
        for key in keys:
            ret[key] = self
        return ret

    def call(self, msg):

        answ_str_stats = [u'Счётчики', u'Счётчики аккаунта']
        answ_str_stats_null = [u'Всё по нулям', u'Всё счётчики по нулям']

        stats = self.vk.method('account.getCounters')

        stats_str = ''

        for key in stats:
            stats_str += u'* ' + key + u' = ' + str(stats[key]) + u'\n'

        if stats_str == '':
            answ = random.choice(answ_str_stats_null) + u'.'
        else:
            answ = random.choice(answ_str_stats) + u': \n' + stats_str

        self.vk.respond(msg, {'message': answ})