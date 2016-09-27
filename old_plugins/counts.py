
import random


class Plugin:
    vk = None

    plugin_type = 'command'

    def __init__(self, vk):
        self.vk = vk
        print('Счетчики')

    def getkeys(self):
        keys = ['счетчики', 'счетчик', 'count', 'статистика', 'стата', 'stats']
        ret = {}
        for key in keys:
            ret[key] = self
        return ret

    def call(self, msg):

        answ_str_stats = ['Счётчики', 'Счётчики аккаунта']
        answ_str_stats_null = ['Всё по нулям', 'Всё счётчики по нулям']

        stats = self.vk.method('account.getCounters')

        stats_str = ''

        for key in stats:
            stats_str += '* ' + key + ' = ' + str(stats[key]) + '\n'

        if stats_str == '':
            answ = random.choice(answ_str_stats_null) + '.'
        else:
            answ = random.choice(answ_str_stats) + ': \n' + stats_str

        self.vk.respond(msg, {'message': answ})
