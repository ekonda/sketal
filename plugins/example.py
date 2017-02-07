from plugin_system import Plugin

plugin = Plugin("Пример плагина",
                usage="тест - пример плагина с аргументами")


# Желательно первой командой указывать основную (она будет в списке команд)
@plugin.on_command('тест')
async def any_name(msg, args):
    await msg.answer(f'Пример плагина. Аргументы - {args}, '
                     f'приложения - {msg.attaches}')
