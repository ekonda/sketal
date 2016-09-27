from say import fmt

from plugin_system import Plugin

plugin = Plugin('Помощь')

@plugin.on_command('помощь', 'помоги', 'команды', 'commands', 'help', 'хелп')
def call(vk, msg, args):
    commands = vk.get_commands()  # тсс, это секрет!!!
    vk.respond(msg, {"message": fmt("Все доступные команды: {', '.join(commands)}.")})