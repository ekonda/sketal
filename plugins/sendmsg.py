from plugin_system import Plugin

plugin = Plugin('Послать сообщение')


@plugin.on_command('написать', 'напиши', 'лс', 'письмо')
def write_msg(vk, msg, args):
    if len(args) > 1:
        if args[0].isdigit():
            uid = int(args[0])
            body = 'Меня тут попросили тебе написать: \n'
            body += ' '.join(arg for arg in args[1:])
            val = {
                # 'user_id':uid,
                'peer_id': uid,
                'message': body
            }
            vk.method('messages.send', val)
            vk.respond(msg, {'message': 'Сообщение успешно отправлено!'})
        else:
            vk.respond(msg, {'message': 'Не могу найти такой ID пользователя'})
    else:
        vk.respond(msg, {'message': 'Введи ID пользователя и сообщение для него'})
