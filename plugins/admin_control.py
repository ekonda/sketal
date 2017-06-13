from database import *
from plugin_system import Plugin

plugin = Plugin('Контроль бота (только для админов)',
                usage=['выключить - выключает бота',
                       'добавить в белый список [id] - добавить пользователя с id в белый список',
                       'убрать из белого списка [id] - убрать пользователя с id из белого списка',
                       'добавить в чёрный список [id] - добавить пользователя с id в чёрный список',
                       'убрать из чёрного списка [id] - убрать пользователя с id из чёрного списка',
                       'сделать админом [id] - добавить пользователя с id в белый список',
                       'убрать из админов [id] - убрать пользователя с id из белого списка',
                       'чёрный список - показать чёрный список'
                       'белый список - показать белый список',
                       'админы - показать админов'])


@plugin.on_command('выключить')
async def shutdown(msg, args):
    if await get_or_none(Role, user_id=msg.user_id, role="admin"):
        await msg.answer('Выключаюсь, мой господин...')
        exit()
    else:
        await msg.answer('Я бы с радостью, но вы не мой администратор :)')


@plugin.on_command('добавить в белый список')
async def add_to_whitelist(msg, args):
    return await add_to_list(msg, args, "whitelisted")


@plugin.on_command('добавить в чёрный список')
async def add_to_admins(msg, args):
    return await add_to_list(msg, args, "blacklisted")


@plugin.on_command('сделать админом')
async def add_to_blacklist(msg, args):
    return await add_to_list(msg, args, "admin")


@plugin.on_command('убрать из белого списка')
async def remove_from_whitelist(msg, args):
    return await remove_from_list(msg, args, "whitelisted")


@plugin.on_command('убрать из чёрного списка')
async def remove_from_blacklist(msg, args):
    return await remove_from_list(msg, args, "blacklisted")


@plugin.on_command('убрать из админов')
async def remove_from_admins(msg, args):
    return await remove_from_list(msg, args, "admin")


@plugin.on_command('чёрный список')
async def show_blacklisted(msg, args):
    return await show_list(msg, args, "blacklisted")


@plugin.on_command('белый список')
async def show_whitelisted(msg, args):
    return await show_list(msg, args, "whitelisted")


@plugin.on_command('админы')
async def show_blacklisted(msg, args):
    return await show_list(msg, args, "admin")


async def show_list(msg, args, role):
    if not await get_or_none(Role, user_id=msg.user_id, role="admin"):
        return

    message = f"Список пользователей {role}:\n"

    for u in await db.execute(Role.select(Role.user_id).where(Role.role == role)):
        message += f"{u.user_id}, "

    return await msg.answer(message)


async def add_to_list(msg, args, role):
    if not await get_or_none(Role, user_id=msg.user_id, role="admin"):
        return

    if not args or not args[0].isdigit():
        return await msg.answer("Вы не указали ID пользователя или указали его неверно!")

    await db.get_or_create(Role, user_id=int(args[0]), role=role)

    if role == "whitelisted":
        await check_white_list(msg.vk.bot)

    return await msg.answer("Готово!")


async def remove_from_list(msg, args, role):
    if not await get_or_none(Role, user_id=msg.user_id, role="admin"):
        return

    if not await get_or_none(Role, user_id=msg.user_id, role=role):
        return

    if not args or not args[0].isdigit():
        return await msg.answer("Вы не указали ID пользователя или указали его неверно!")

    await db.execute(Role.delete().where(Role.user_id == int(args[0])))

    if role == "whitelisted":
        await check_white_list(msg.vk.bot)

    return await msg.answer("Готово!")
