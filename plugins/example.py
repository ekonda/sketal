from plugin_system import Plugin

plugin = Plugin("Пример плагина")


# Желательно первой командой указывать основную (она будет в списке команд)
@plugin.on_command('тестовый плагин', 'пример плагина')
async def any_name(vk, msg, args):
    await vk.respond(msg, {'message': 'Пример плагина (аргументы - ' + str(args) + ' )'})
