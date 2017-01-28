from plugin_system import Plugin

plugin = Plugin('Список плагинов',
                usage='плагины - показать список загруженных плагинов')


@plugin.on_command('плагины')
async def call(msg, args):
    await msg.answer('Загруженные плагины:\n' + '\n'.join(
        pl.name for pl in msg.vk.get_plugins()
    ))
