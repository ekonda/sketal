from plugin_system import Plugin

plugin = Plugin('Нет')


@plugin.on_command('нет', 'nope')
async def call(vk, msg, args):
    await vk.respond(msg, {'message': '🌚',
                           'attachment': 'video168815191_168798454'})
