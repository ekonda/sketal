import random

from plugin_system import Plugin

plugin = Plugin('Счётчики')

answ_str_stats = ['Счётчики', 'Счётчики аккаунта']
answ_str_stats_null = ['Всё по нулям', 'Всё счётчики по нулям']


@plugin.on_command('счётчики', 'счётчик', 'статистика', 'покажи стату', 'стата')
def stats_good(vk, msg, args):
    stats = vk.method('account.getCounters')
    stats_str = ''

    for key in stats:
        stats_str += '* ' + key + ' = ' + str(stats[key]) + '\n'

    if stats_str == '':
        answ = random.choice(answ_str_stats_null) + '.'
    else:
        answ = random.choice(answ_str_stats) + ': \n' + stats_str

    vk.respond(msg, {'message': answ})
