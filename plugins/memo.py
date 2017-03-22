from plugin_system import Plugin
usage=['запомни [строка] - запомнить строку',
                      'напомни - напомнить строку']

plugin = Plugin('Блокнот', usage=usage)

memoes = {}


@plugin.on_command('запомни', 'запиши')
async def memo_write(msg, args):
    string = ' '.join(args)
    memoes[msg.id] = string
    await msg.answer('Вроде запомнил...')


@plugin.on_command('напомни', 'вспомни')
async def memo_read(msg, args):
    string = memoes.get(msg.id, "Ничего")
    await msg.answer('Вот что я вспомнил:\n' + string)
