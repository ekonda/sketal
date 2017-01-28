from plugin_system import Plugin

plugin = Plugin('Блокнот',
                usage='запомни [строка] - запомнить строку\n'
                      'напомни - напомнить строку')

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
