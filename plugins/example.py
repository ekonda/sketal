from plugin_system import Plugin

plugin = Plugin("Пример плагина",
                usage="тест - пример плагина с аргументами")


# Функция будет выполняться при загрузки плагинов.
# Обезательно принимает один аргумент: объект VkPlus
@plugin.on_init()
async def init(vk):
    # Объект plugin.data будет автоматически сохраняться при выключении бота
    # и загружаться при старте автоматически. Избегайте крупных объектов
    if "some_data" not in plugin.data:
        plugin.data["some_data"] = {}


# Функция будет выполняться, когда пользователь введёт команду(ы),
# указанные в аргументах on_command
# Обезательно принимает 2 аргумента - команда и аргументы
# Желательно первой командой указывать основную (она будет в списке команд)
@plugin.on_command('тест', 'test')
async def command(msg, args):
    # msg.body - для полного текста сообщения

    if msg.brief_attaches: # короткий список вложений
        attachments = await msg.full_attaches # полные вложения
        attaches = "\n".join([str(attach) for attach in attachments])
    else:
        attaches = ""

    await msg.answer(f'Пример плагина.\n' +
                     f'Аргументы - {args}\n' +
                     (f'Вложения:\n{attaches}' if attaches else ""))
