from plugin_system import Plugin

plugin = Plugin('Запоминатель')

memoes = {}


@plugin.on_command('запомни', 'запиши', 'не забудь')
def memo(vk, msg, args):
    string = ' '.join(args)
    if 'chat_id' in msg:
        memoes[msg['chat_id']] = string
    else:
        memoes[msg['user_id']] = string
    vk.respond(msg, {'message': 'Вроде запомнил...'})


@plugin.on_command('напомни', 'вспомни', 'посмотри блокнот')
def memo(vk, msg, args):
    string = ''
    if 'chat_id' in msg:
        string = memoes[msg['chat_id']]
    else:
        string = memoes[msg['user_id']]
    vk.respond(msg, {'message': 'Вот что я вспомнил:\n' + string})
