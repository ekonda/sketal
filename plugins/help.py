from say import fmt

from plugin_system import Plugin

plugin = Plugin('Помощь')

@plugin.on_command('помощь', 'помоги', 'команды', 'хелп')
def call(vk, msg, args):
    commands = [plug.first_command for plug in vk.get_plugins()]
    vk.respond(msg, {"message": fmt("Доступные команды: {', '.join(commands)}.")})