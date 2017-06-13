from database import *
from plugin_system import Plugin

plugin = Plugin('Посылка для пользователей',
                usage=['объявление - получить объявление, оставленное администратором',
                       'Команды админов:',
                       'объявление оставить [текст] - оставить объявление',
                       'объявление список - показать тех, что может получить посылку',
                       'объявление список добавить [id] - добавить пользователя с id из получателей',
                       'объявление список убрать [id] - убрать пользователя с id из получателей',
                       'объявление список очистить - очистить список получателей'])


NOT_IN_LIST = "Вы не в списке!"


@plugin.on_command('объявление')
async def get(msg, args):
    if await get_or_none(ListForMail, user_id=msg.user_id):
        status, created = await db.get_or_create(BotStatus, id=0)

        if not status.mail_data:
            return await msg.answer("Пусто!")

        await msg.answer(status.mail_data)

    else:
        await msg.answer(NOT_IN_LIST)


@plugin.on_command('объявление оставить')
async def leave(msg, args):
    if not await get_or_none(Role, user_id=msg.user_id, role="admin"):
        return

    status, created = await db.get_or_create(BotStatus, id=0)
    status.mail_data = msg.text
    await db.update(status)

    return await msg.answer("Готово!")


@plugin.on_command('объявление список')
async def show_list(msg, args):
    if not await get_or_none(Role, user_id=msg.user_id, role="admin"):
        return

    message = "Список людей, которые могут получить сообщение:\n"

    c = 1
    for u in await db.execute(ListForMail.select()):
        message += f"{c}. http://vk.com/id{u.user_id} ({str(u.date)}))"
        c += 1

    return await msg.answer(message)


@plugin.on_command('объявление список добавить')
async def add_to_list(msg, args):
    if not await get_or_none(Role, user_id=msg.user_id, role="admin"):
        return

    if not args or not args[0].isdigit():
        return await msg.answer("Вы не указали ID пользователя или указали его неверно!")

    await db.get_or_create(ListForMail, user_id=int(args[0]))

    return await msg.answer("Готово!")


@plugin.on_command('объявление список убрать')
async def remove_from_list(msg, args):
    if not await get_or_none(Role, user_id=msg.user_id, role="admin"):
        return

    if not args or not args[0].isdigit():
        return await msg.answer("Вы не указали ID пользователя или указали его неверно!")

    await db.execute(ListForMail.delete().where(ListForMail.user_id == int(args[0])))

    return await msg.answer("Готово!")


@plugin.on_command('объявление список очистить')
async def clear_list(msg, args):
    if not await get_or_none(Role, user_id=msg.user_id, role="admin"):
        return

    await db.execute(ListForMail.delete())

    return await msg.answer("Готово!")

