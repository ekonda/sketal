from plugin_system import Plugin

plugin = Plugin('Список плагинов')


@plugin.on_command('плагины', 'список плагинов')
async def call(msg, args):
    await msg.answer('Загруженные плагины:\n' + ', '.join(pl.name for pl in msg.vk.get_plugins()))
