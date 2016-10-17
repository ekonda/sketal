from plugin_system import Plugin

plugin = Plugin('Нет')


@plugin.on_command('нет', 'nope')
async def call(msg, args):
    await msg.answer('🌚', attachment='video168815191_168798454')
