from plugin_system import Plugin

plugin = Plugin('Послать сообщение')


@plugin.on_command('написать', 'напиши', 'лс', 'письмо')
async def write_msg(msg, args):
    if len(args):
        if args[0].isdigit():
            uid = int(args[0])
            body = 'Меня тут попросили тебе написать: \n'
            body += ' '.join(arg for arg in args[1:])
            val = {
                # 'user_id':uid,
                'peer_id': uid,
                'message': body
            }
            await msg.vk.method('messages.send', val)
            await msg.answer('Сообщение успешно отправлено!')
        else:
            await msg.answer('Не могу найти такой ID пользователя')
    else:
        await msg.answer('Введите ID пользователя и сообщение для него')
