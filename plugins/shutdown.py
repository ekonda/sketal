from plugin_system import Plugin
from settings import ADMINS

plugin = Plugin('Выключение',
                usage='выключить - выключает бота (только для админов)')


@plugin.on_command('выключить')
async def shutdown(msg, args):
    uid = msg.id
    if uid in ADMINS:
        await msg.answer('Выключаюсь, мой господин...')
        exit()
    else:
        await msg.answer('Я бы с радостью, но вы не мой администратор :)')
