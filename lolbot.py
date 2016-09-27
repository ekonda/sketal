import builtins
from os.path import abspath, isfile
import shutil
import traceback  # используется в say()
from say import say, fmt

from plugin_system import PluginSystem
from vkplus import VkPlus

builtins.print = say  # Переопределить print функцией say (совместима с print)


class Bot(object):
    '''Главный класс бота, создан для упрощённой работы с переменными'''

    # Функция для упрощённого вывода зелёных сообщений
    def good(self, string):
        say(string, style='green')

    def __init__(self):
        # По умолчанию все сообщения будут жирные и синие :)
        say.set(style='blue+bold')

        self.last_message_id = 0
        self.init_settings()
        self.vk_init()
        self.plugin_init()
        self.good('Приступаю к приему сообщений')

        self.run()

    def init_settings(self):
        '''Функция инициализации файла настроек и его создания'''
        # Если у нас есть только settings.py.sample
        if isfile('settings.py.sample') and not isfile('settings.py'):
            try:
                shutil.copy('settings.py.sample', 'settings.py')
            except:
                say('У меня нет прав писать в текущую директорию, '
                    'проверьте ваши права на неё!', style='red')
                exit()
            self.good('Был создан файл settings.py, пожалуйста, измените значения на Ваши!')
            exit()
        # Если у нас уже есть settings.py
        elif isfile('settings.py'):
            import settings
            try:
                self.BLACKLIST = settings.blacklist
                self.PREFIXES = settings.prefixes
                self.token = settings.vk_access_token
                self.app_id = settings.vk_app_id
            except:
                say('Проверьте содержание файла settings.py, возможно вы удалили что-то нужное!')
                exit()
        # Если не нашли ни settings.py, ни settings.py.sample
        else:
            say('settings.py и settings.py.sample не найдены, возможно вы их удалили? ', style='red+bold')
            exit()

    def vk_init(self):
        # Авторизуемся в ВК
        say('Авторизация в вк...', style='yellow')
        self.vk = VkPlus(self.token, self.app_id)
        self.ANSWER_VALUES = {
            'out': 0,
            'offset': 0,
            'count': 20,
            'time_offset': 50,
            'filters': 0,
            'preview_length': 0,
            'last_message_id': self.last_message_id
        }
        self.good('Успешная авторизация')

    def plugin_init(self):
        # Подгружаем плагины
        say.title("Загрузка плагинов:")
        self.plugin_system = PluginSystem(folder=abspath('plugins'))
        self.plugin_system.register_commands()
        # Чтобы плагины могли получить список команд
        self.vk.get_commands = self.plugin_system.get_commands
        say.title("Загрузка плагинов завершена")

    def run(self):
        while True:
            self.check_messages()

    def check_messages(self):

        response = self.vk.method('messages.get', self.ANSWER_VALUES)
        if response is not None and response['items']:
            self.last_message_id = response['items'][0]['id']
            for item in response['items']:
                # Если сообщение не прочитано и ID пользователя не в чёрном списке бота
                if item['read_state'] == 0 and item['user_id'] not in self.BLACKLIST:
                    self.execute_command(item)  # выполняем команду
                    self.vk.mark_as_read(item['id'])  # Помечаем прочитанным

    def execute_command(self, message):
        if not message['body']:  # Если строка пустая
            return
        words = message['body'].split()  # Делим строку на список слов
        first_word = words[0]
        if words[0].startswith(self.PREFIXES):  # Если наш бот должен реагировать на этот префикс
            if len(words) > 1:  # Если есть команда (может и аргументы)
                command = words[1].lower()  # Получаем команду (и приводим в нижний регистр)
                arguments = words[2:]  # Получаем аргументы срезом
                if 'chat_id' in message:
                    say("Команда из конференции ({message['chat_id']}) > {message['body']}")
                elif 'user_id' in message:
                    say("Команда из ЛС (id{message['user_id']}) > {message['body']}")
                try:
                    self.plugin_system.call_command(command, self.vk, message, arguments)
                except:
                    self.vk.respond(message, {
                        "message": fmt(
                            "{self.vk.anti_flood()}. Произошла ошибка при выполнении команды <{command}>, "
                            "пожалуйста, сообщите об этом разработчику!")
                    })

                    say(
                        "Произошла ошибка при вызове команды '{command}'. "
                        "Сообщение: '{message['body']}' с параметрами {arguments}. "
                        "Ошибка:\n{traceback.format_exc()}",
                        style='red')
                    # print(message, command, arguments) -> for debug only


if __name__ == '__main__':
    bot = Bot()
