from plugin_system import Plugin
from settings import ADMINS

plugin = Plugin('Выключение',
                description='Выключить бота (только для администраторов)')


@plugin.on_command('выключить', 'выкл', 'вырубись')
async def shutdown(msg, args):
    uid = msg.id
    if uid in ADMINS:
        await msg.answer('Выключаюсь...')
        exit()
    else:
        await msg.answer('Хорошая попытка, обычный пользователь!')
