import hues

from plugin_system import Plugin

plugin = Plugin("Отправка анонимного сообщения",
                usage=["анонимно [id] [сообщение] - написать анонимное сообщение пользователю"
                       "(посылать можно только текст и/или фото)",
                       "неполучатьанонимки - не получать анонимные сообщения",
                       "получатьанонимки - получать анонимные сообщения"])


DISABLED = ('https', 'http', 'com', 'www', 'ftp', '://')


def check_links(string):
    return any(x in string for x in DISABLED)


@plugin.on_init()
def init(vk):
    if "donotdisturb" not in plugin.data:
        plugin.data["donotdisturb"] = {}
    else:
        for k in plugin.data["donotdisturb"]:
            plugin.data["donotdisturb"][int(k)] = plugin.data["donotdisturb"].pop(k)


@plugin.on_command('анонимка', 'анонимно')
async def anonymously(msg, args):
    text_required = True
    for k, v in msg.brief_attaches.items():
        if '_type' in k and v == "photo":
            text_required = False
            break

    if len(args) < 2 and text_required:
        return await msg.answer('Введите ID пользователя и сообщение для него.')

    sender_id = msg.id
    possible_id = args.pop(0)

    if not possible_id.isdigit():
        uid = await msg.vk.resolve_name(possible_id)
    else:
        uid = int(possible_id)

    if not uid:
        return await msg.answer('Проверьте правильность введёного ID пользователя.')

    if sender_id == uid:
        return await msg.answer('Зачем мне отправлять сообщение вам?!')

    data = ' '.join(args)

    if check_links(data):
        return await msg.answer('В сообщении были обнаружены ссылки!')

    if plugin.data["donotdisturb"].get(uid, False):
        return await msg.answer('Этот пользователь попросил его не беспокоить!')

    message = "Вам анонимное сообщение!\n"

    if data:
        message += data + "\n"

    if not text_required:
        full = await msg.full_attaches
        if full:
            message += "Вложения:\n".join(m.link for m in full)

    val = {
        'peer_id': uid,
        'message': message
    }

    result = await msg.vk.method('messages.send', val)
    if not result:
        return await msg.answer('Сообщение не удалось отправить!')
    await msg.answer('Сообщение успешно отправлено!')


@plugin.on_command('неполучатьанонимки')
async def silenceon(msg, args):
    plugin.data["donotdisturb"][msg.id] = True

    await msg.answer('Вы не будете получать сообщения!')


@plugin.on_command('получатьанонимки')
async def silenceoff(msg, args):
    plugin.data["donotdisturb"][msg.id] = False

    await msg.answer('Вы будете получать все сообщения!')
