from plugin_system import Plugin

plugin = Plugin('Помощь',
                usage='команды - узнать список доступных команд')


@plugin.on_command('команды', 'помоги', 'помощь')
async def call(msg, args):
    usages = '\n&#9899;'.join(pl.usage for pl in msg.vk.get_plugins() if pl.usage)
    await msg.answer(f"&#9889; Доступные команды: \n{usages}")
