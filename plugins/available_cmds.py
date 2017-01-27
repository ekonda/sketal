from plugin_system import Plugin

plugin = Plugin('Помощь')


@plugin.on_command('помощь', 'помоги', 'команды', 'хелп')
async def call(msg, args):
    commands = [plug.first_command for plug in msg.vk.get_plugins()]
    await msg.answer("Доступные команды: {}.".format(', '.join(commands)))
