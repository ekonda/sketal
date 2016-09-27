from say import fmt

from plugin_system import Plugin

plugin = Plugin("Пример плагина")

# Желательно первой командой указывать основную (она будет в списке команд)
@plugin.on_command('тестовыйплагин', 'примерплагина')
def anynameoffunctioncanbehere(vk, raw_message, args):
    print("OK!")
    vk.respond(raw_message, {'message': fmt('Пример плагина (аргументы - {args})')})
