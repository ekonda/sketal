from plugin_system import Plugin

plugin = Plugin('Помощь',
                usage='команды - узнать список доступных команд')


@plugin.on_command('команды', 'помоги', 'помощь')
async def call(msg, args):
    usages = [pl.usage for pl in msg.vk.get_plugins() if pl.usage]
    # Конвертируем 2D список в 1D
    usages = [usg for usage in usages for usg in usage]
    usages = '\n\n✏ '.join(usages)

    await msg.answer(f"⭐ Доступные команды: \n\n✏ {usages}")
