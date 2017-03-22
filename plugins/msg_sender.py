import re

from plugin_system import Plugin

plugin = Plugin('Послать сообщение',
                usage='напиши [id] [сообщение] - написать сообщение пользователю')


URL_REGEX = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+''
URL_REGEX = re.compile(URL_REGEX)
async def check_links(vk, string):
    processing = False
    banned = False
    urls = URL_REGEX.findall(string)
    for link in urls:
        result = await vk.method('utils.checkLink', data=dict(url=link))
        status = result['status']
        if status == 'banned':
            banned = True
            break
        if status == 'processing':
            processing = True
            continue
    return processing, banned




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
    data = ' '.join(args)

    processing = True
    while processing:
        processing, banned = await check_links(msg.vk, data)
        if banned:
            return await msg.answer('Одна из ссылок в сообщении небезопасна!')

    val = {
        'peer_id': uid,
        'message': data
    }

    result = await msg.vk.method('messages.send', val)
    if not result:
        return await msg.answer('Сообщение не удалось отправить!')
    await msg.answer('Сообщение успешно отправлено!')
