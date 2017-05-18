from plugin_system import Plugin

plugin = Plugin("Пример плагина",
                usage=["тест - пример плагина с аргументами"])


# Чтобы функция выполнялась переодически и без остановки смотри пример в friends.py

# Функция выполняется при загрузке плагинов.
# Обязательно принимает один аргумент: объект VkPlus
@plugin.on_init()
async def init(vk):
    # Есть plugin.temp_data, хранит в себе
    # что-нибудь нужное вам
    if "some_data" not in plugin.temp_data:
        plugin.temp_data["some_data"] = {}


# Если необходимо выполнить какую-то длительную задачу(которую нелья переписать как корутину),
# не блокируя исполнения команд другими пользователями - ипользуйте plugin.process_pool:
# result = await loop.run_in_executor(plugin.process_pool, long_function, argument1, argument2)


# Функция будет выполняться, когда пользователь введёт команду(ы),
# указанные в аргументах on_command
# Обязательно принимает 2 аргумента - команда и аргументы
# Желательно первой командой указывать основную (она будет в списке команд)
@plugin.on_command('тест', 'test')
async def command(msg, args):
    # msg.text - для полного текста сообщения без команды
    # msg.body - для полного текста сообщения
    # msg.user_id - id пользоватлея, который обратился к боту

    if msg.brief_attaches: # короткий список вложений
        attachments = await msg.full_attaches # полные вложения
        attaches = "\n".join(str(attach) for attach in attachments)
    else:
        attaches = ""

    await msg.answer(f'Пример плагина.\n' +
                     f'Аргументы - {args}\n' +
                     (f'Вложения:\n{attaches}' if attaches else ""))
