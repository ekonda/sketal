from plugin_system import Plugin

plugin = Plugin('Запоминатель')

memoes = {}


@plugin.on_command('запомни', 'запиши', 'не забудь')
async def memo_write(msg, args):
    string = ' '.join(args)
    if msg.conf:
        memoes[msg.cid] = string
    else:
        memoes[msg.uid] = string
    await msg.answer('Вроде запомнил...')


@plugin.on_command('напомни', 'вспомни', 'посмотри блокнот')
async def memo_read(msg, args):
    string = ''
    if msg.conf:
        string = memoes.get(msg.cid, "Ничего")
    else:
        string = memoes.get(msg.uid, "Ничего")
    await msg.answer('Вот что я вспомнил:\n' + string)
