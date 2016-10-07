from say import fmt

from plugin_system import Plugin

plugin = Plugin("Пример плагина")


# Желательно первой командой указывать основную (она будет в списке команд)
@plugin.on_command('тестовый плагин', 'пример плагина')
def anynameoffunctioncanbehere(vk, msg, args):
    args = ''.join(args)
    print("OK!")
    vk.respond(msg, {'message': 'Пример плагина (аргументы - ' + args})
