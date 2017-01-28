from plugin_system import Plugin

plugin = Plugin('Послать сообщение',
                usage='написать [id] [сообщение] - написать сообщение пользователю с ID id')


@plugin.on_command('написать', 'напиши', 'лс', 'письмо')
async def write_msg(msg, args):
    if len(args) < 2:
        return await msg.answer('Введите ID пользователя и сообщение для него.')
    possible_id = args.pop(0)
    if not possible_id.isdigit():
        uid = await msg.vk.resolve_name(possible_id)
    else:
        uid = int(possible_id)
    if not uid:
        await msg.answer('Проверьте правильность введёного ID пользователя.')
        return
    body = 'Меня тут попросили тебе написать: \n' + ' '.join(args)
    val = {
        'peer_id': uid,
        'message': body
    }
    await msg.vk.method('messages.send', val)
    await msg.answer('Сообщение успешно отправлено!')
