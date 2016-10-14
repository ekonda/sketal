from plugin_system import Plugin

plugin = Plugin('Выключение', description='Выключить бота (только для админов)')


@plugin.on_command('выключить', 'выкл', 'вырубись')
async def shutdown(vk, msg, args):
    uid = msg.get('user_id', None)
    if not uid:
        return
    if str(uid) == '170831732':
        await vk.respond(msg, {'message': 'Выключаюсь...'})
        exit()
