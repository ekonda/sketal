from plugin_system import Plugin

plugin = Plugin('Выключение', description='Выключить бота (только для админов)')


@plugin.on_command('выключить', 'выкл', 'вырубись')
async def shutdown(msg, args):
    uid = msg.id
    if uid == 170831732:
        await msg.answer('Выключаюсь...')
        exit()
