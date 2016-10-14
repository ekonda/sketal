from plugin_system import Plugin

plugin = Plugin('Список плагинов')


@plugin.on_command('плагины', 'список плагинов')
async def call(vk, msg, args):
    await vk.respond(msg, {'message': 'Загруженные плагины:\n' +
                                      ', '.join(plugin.name for plugin in vk.get_plugins())
                           })
