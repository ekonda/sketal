from plugin_system import Plugin

plugin = Plugin('Послать сообщение',
                usage='напиши [id] [сообщение] - написать сообщение пользователю')


@plugin.on_command('написать', 'напиши', 'лс', 'письмо', group=False)
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
    val = {
        'peer_id': uid,
        'message': ' '.join(args)
    }
    result = await msg.vk.method('messages.send', val)
    if not result:
        return await msg.answer('Сообщение не удалось отправить!')
    await msg.answer('Сообщение успешно отправлено!')
