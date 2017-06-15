from database import *
from plugin_system import Plugin

plugin = Plugin("Отправка сообщения",
                usage=["напиши [id] [сообщение] - написать сообщение пользователю",
                       "анонимно [id] [сообщение] - написать анонимное сообщение пользователю"
                       "(посылать можно только текст и/или фото)",
                       "не беспокоить - не получать сообщения",
                       "беспокоить - получать сообщения"],
                need_db=True)


DISABLED = ('https', 'http', 'com', 'www', 'ftp', '://')


def check_links(string):
    return any(x in string for x in DISABLED)


@plugin.on_init()
def init(vk):
    pass


@plugin.on_command('анонимка', 'анонимно')
async def anonymously(msg, args):
    text_required = True
    for k, v in msg.brief_attaches.items():
        if '_type' in k and v == "photo":
            text_required = False
            break

    if len(args) < 2 and text_required:
        return await msg.answer('Введите ID пользователя и сообщение для него.')

    sender_id = msg.user_id
    possible_id = args.pop(0)

    if not possible_id.isdigit():
        uid = await msg.vk.resolve_name(possible_id)
    else:
        uid = int(possible_id)

    if not uid:
        return await msg.answer('Проверьте правильность введёного ID пользователя.')

    if sender_id == uid:
        return await msg.answer('Зачем мне отправлять сообщение вам?!')

    if await get_or_none(Ignore, ignored=sender_id, ignored_by=uid):
        return await msg.answer('Вы находитесь в чёрном списке у этого пользователя!')

    user = await get_or_none(User, uid=uid)
    if user and user.do_not_disturb:
        return await msg.answer('Этот пользователь попросил его не беспокоить!')

    data = ' '.join(args)

    if check_links(data):
        return await msg.answer('В сообщении были обнаружены ссылки!')

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


@plugin.on_command('админу')
async def to_admin(msg, args):
    sender_id = msg.user_id

    for role in await db.execute(Role.select().where(Role.role == "admin")):
        if await get_or_none(Ignore, ignored=sender_id, ignored_by=role.user_id):
            return await msg.answer('Вы находитесь в чёрном списке у этого пользователя!')

        user = await get_or_none(User, uid=role.user_id)
        if user and user.do_not_disturb:
            return await msg.answer('Этот пользователь попросил его не беспокоить!')

        data = ' '.join(args)

        if check_links(data):
            return await msg.answer('В сообщении были обнаружены ссылки!')

        sender_data = await msg.vk.method('users.get', {'user_ids': msg.user_id, 'name_case': "gen"})
        sender_data = sender_data[0]

        val = {
            'peer_id': role.user_id,
            'message': f"Вам сообщение от {sender_data['first_name']} {sender_data['last_name']}!\n\"{data}\"",
        }

        if "attach1" in msg.brief_attaches:
            val['attachment'] = ",".join(str(x) for x in await msg.full_attaches)

        result = await msg.vk.method('messages.send', val)
        if not result:
            return await msg.answer('Сообщение не удалось отправить!')
        await msg.answer('Сообщение успешно отправлено!')


@plugin.on_command('написать', 'напиши', 'лс', 'письмо')
async def write_msg(msg, args):
    if (len(args) != 1 or not msg.brief_attaches) and len(args) < 2:
        return await msg.answer('Введите ID пользователя и сообщение для него.')

    sender_id = msg.user_id
    possible_id = args.pop(0)

    if not possible_id.isdigit():
        uid = await msg.vk.resolve_name(possible_id)
    else:
        uid = int(possible_id)

    if not uid:
        return await msg.answer('Проверьте правильность введёного ID пользователя.')

    if sender_id == uid:
        return await msg.answer('Зачем мне отправлять сообщение самому себе?!')

    if await get_or_none(Ignore, ignored=sender_id, ignored_by=uid):
        return await msg.answer('Вы находитесь в чёрном списке у этого пользователя!')

    user = await get_or_none(User, uid=uid)
    if user and user.do_not_disturb:
        return await msg.answer('Этот пользователь попросил его не беспокоить!')

    data = ' '.join(args)

    if check_links(data):
        return await msg.answer('В сообщении были обнаружены ссылки!')

    sender_data = await msg.vk.method('users.get', {'user_ids': msg.user_id, 'name_case': "gen"})
    sender_data = sender_data[0]

    val = {
        'peer_id': uid,
        'message': f"Вам сообщение от {sender_data['first_name']} {sender_data['last_name']}!\n\"{data}\"",
    }

    if "attach1" in msg.brief_attaches:
        val['attachment'] = ",".join(str(x) for x in await msg.full_attaches)

    result = await msg.vk.method('messages.send', val)
    if not result:
        return await msg.answer('Сообщение не удалось отправить!')
    await msg.answer('Сообщение успешно отправлено!')



@plugin.on_command('скрыть')
async def hide(msg, args):
    if len(args) < 1:
        return await msg.answer('Введите ID пользователя для игнорирования.')

    sender_id = msg.user_id
    ignore_id = args.pop()

    if not ignore_id.isdigit():
        uid = await msg.vk.resolve_name(ignore_id)
    else:
        uid = int(ignore_id)

    if not uid:
        return await msg.answer('Проверьте правильность введёного ID пользователя.')

    await db.create_or_get(Ignore, ignored=uid, ignored_by=sender_id)

    await msg.answer(f'Вы не будете получать сообщения от {ignore_id}!')


@plugin.on_command('показать')
async def show(msg, unignore):
    if len(unignore) < 1:
        return await msg.answer('Введите ID пользователя, которого вы хотите убрать из игнора.')

    sender_id = msg.user_id
    unignore_id = unignore.pop()

    if not unignore_id.isdigit():
        uid = await msg.vk.resolve_name(unignore_id)
    else:
        uid = int(unignore_id)

    if not uid:
        return await msg.answer('Проверьте правильность введёного ID пользователя.')

    await db.execute(Ignore.delete().where(
        (Ignore.ignored == uid) & (Ignore.ignored_by == sender_id)
    ))

    await msg.answer(f'Теперь {unignore_id} сможет отправлять вам сообщения!')


@plugin.on_command('не беспокоить')
async def do_not_disturb(msg, args):
    user = await get_or_none(User, uid=msg.user_id)

    if not user:
        return await msg.answer('Вы не существуете!\n(или у бота проблемы с базой данных)')

    user.do_not_disturb = True

    await db.update(user)

    await msg.answer('Вы не будете получать сообщения!')


@plugin.on_command('беспокоить')
async def do_disturb(msg, args):
    user = await get_or_none(User, uid=msg.user_id)

    if not user:
        return await msg.answer('Вы не существуете!\n(или у бота проблемы с базой данных)')

    user.do_not_disturb = False

    await db.update(user)

    await msg.answer('Вы будете получать все сообщения!')
