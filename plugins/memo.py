from database import *
from plugin_system import Plugin


plugin = Plugin('Блокнот',
                usage=['запомни [строка] - запомнить строку',
                       'напомни - напомнить строку'],
                need_db=True)


@plugin.on_command('запомни', 'запиши')
async def memo_write(msg, args):
    string = ' '.join(args)

    user = await get_or_none(User, uid=msg.user_id)

    if not user:
        return await msg.answer('Вас не существует или база данных бота не настроена.')

    user.memory = string

    await db.update(user)

    await msg.answer('Вроде запомнил...')


@plugin.on_command('напомни', 'вспомни')
async def memo_read(msg, args):
    user = await get_or_none(User, uid=msg.user_id)

    if not user:
        return await msg.answer('Вас не существует или база данных бота не настроена.')

    if not user.memory:
        await msg.answer('Я ничего не вспомнил!')
    else:
        await msg.answer('Вот что я вспомнил:\n' + user.memory)
