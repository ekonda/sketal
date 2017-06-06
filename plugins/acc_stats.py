from plugin_system import Plugin

plugin = Plugin('Счётчики',
                usage='счётчики - узнать статистику аккаунта')

answ_str_stats = ['Счётчики', 'Счётчики аккаунта']
answ_str_stats_null = ['Всё по нулям', 'Всё счётчики по нулям']


@plugin.on_command('счётчики', 'счётчик', 'статистика', 'стата', group=False)
async def stats_good(msg, args):
    stats = await msg.vk.method('account.getCounters')
    data = '\n'.join('{} = {}'.format(name, count)
                     for name, count in stats.items())
    if not data:
        answ = "Всё по нулям"
    else:
        answ = "Счётчики аккаунта:\n" + data

    await msg.answer(answ)
