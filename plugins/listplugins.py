from plugin_system import Plugin


plugin = Plugin('Список плагинов')


@plugin.on_command('плагины')
def call(vk, msg, args):
    vk.respond(msg, {'message': 'Загруженные плагины:\n' +
                                ', '.join(plugin.name for plugin in vk.get_plugins())
                    })
