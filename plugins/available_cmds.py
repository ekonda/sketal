from plugin_system import Plugin

plugin = Plugin('Помощь',
                usage='команды - узнать список доступных команд')


@plugin.on_command('команды', 'помоги', 'помощь')
async def call(msg, args):
    usages = '\n💎'.join(pl.usage for pl in msg.vk.get_plugins() if pl.usage)
    await msg.answer("⚡ Доступные команды: \n{}".format(usages))
