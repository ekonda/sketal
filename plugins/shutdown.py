from plugin_system import Plugin
from settings import ADMINS

plugin = Plugin('Выключение',
                usage='выключить - выключает бота (только для админов)')


@plugin.on_command('выключить', 'выкл', 'вырубись')
async def shutdown(msg, args):
    uid = msg.id
    if uid in ADMINS:
        await msg.answer('Выключаюсь...')
        exit()
    else:
        await msg.answer('Хорошая попытка, обычный пользователь!')
