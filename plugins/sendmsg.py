from plugin_system import Plugin

plugin = Plugin('Послать сообщение')


@plugin.on_command('написать', 'напиши', 'лс', 'письмо')
async def write_msg(msg, args):
    if not len(args):
        return await msg.answer('Введите ID пользователя и сообщение для него')
    if not args[0].isdigit():
        uid = await msg.vk.resolve_name(args[0])
    else:
        uid = int(args[0])
    if not uid:
        await msg.answer('Не могу найти такой ID пользователя')
        return
    body = 'Меня тут попросили тебе написать: \n'
    body += ' '.join(arg for arg in args[1:])
    val = {
        # Возможность посылать в беседы и в обычный чат одновременно
        'peer_id': uid + 2000000000 if (uid - 2000000000) > 0 else uid,
        'message': body
    }
    await msg.vk.method('messages.send', val)
    await msg.answer('Сообщение успешно отправлено!')
