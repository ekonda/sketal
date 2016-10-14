from plugin_system import Plugin

plugin = Plugin('Помощь')


@plugin.on_command('помощь', 'помоги', 'команды', 'хелп')
async def call(vk, msg, args):
    commands = [plug.first_command for plug in vk.get_plugins()]
    await vk.respond(msg, {"message": "Доступные команды: {}.".format(', '.join(commands))})
