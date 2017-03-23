import publicsuffixlist
psl = publicsuffixlist.PublicSuffixList()
from plugin_system import Plugin

plugin = Plugin('Послать сообщение',
                usage='напиши [id] [сообщение] - написать сообщение пользователю')



DISABLED = ('https', 'http', 'com', 'www', 'ftp', '://')
def check_links(string):
    return any(x in string for x in DISABLED) or bool(psl.privatesuffix(string))

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
    data = ' '.join(args)

    if check_links(data):
        return await msg.answer('В сообщении были обнаружены ссылки!')

    val = {
        'peer_id': uid,
        'message': data
    }

    result = await msg.vk.method('messages.send', val)
    if not result:
        return await msg.answer('Сообщение не удалось отправить!')
    await msg.answer('Сообщение успешно отправлено!')
