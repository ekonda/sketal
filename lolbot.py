import builtins
from os.path import abspath, isfile
import shutil
import traceback  # используется в say()

import time
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

                if settings.vk_access_token:
                    self.is_token = True
                    self.token = settings.vk_access_token
                elif settings.vk_login and settings.vk_password:
                    self.is_token = False
                    self.vk_login = settings.vk_login
                    self.vk_password = settings.vk_password
                else:
                    say('Проверьте, что у вас заполнены vk_login и vk_password, или vk_access_token!'
                        '\nБез них бот работать НЕ СМОЖЕТ (ему же надо сидеть с какого-нибудь аккаунта?)')
                    exit()
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

        if self.is_token:
            self.vk = VkPlus(token=self.token)
        if not self.is_token:
            self.vk = VkPlus(login=self.vk_login, password=self.vk_password)

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
        # Чтобы плагины могли получить список плагинов
        self.vk.get_plugins = self.plugin_system.get_plugins
        say.title("Загрузка плагинов завершена")

    def run(self):
        while True:
            self.check_messages()

    def check_messages(self):
        time.sleep(0.05)
        response = self.vk.method('messages.get', self.ANSWER_VALUES)
        if response is not None and response['items']:
            self.last_message_id = response['items'][0]['id']
            for item in response['items']:
                # Если сообщение не прочитано и ID пользователя не в чёрном списке бота
                if item['read_state'] == 0 and item['user_id'] not in self.BLACKLIST:
                    self.check_if_command(item)  # выполняем команду
                    self.vk.mark_as_read(item['id'])  # Помечаем прочитанным

    def check_if_command(self, answer):
        if not answer['body']:  # Если строка пустая
            return
        message_string = answer['body']

        # Если префикс есть в начале строки, убираем его
        for prefix in self.PREFIXES:
            if message_string.startswith(prefix):
                message_string = message_string.replace(prefix, '')
                break
        # Если нет префикса
        else:
            return

        words = message_string.split()  # Делим строку на список слов

        if len(words) < 1:  # Если нет команды, сразу прекращаем выполнение
            return

        command = words[0].lower()  # Получаем команду (и приводим в нижний регистр)
        arguments = words[1:]  # Получаем аргументы срезом

        if 'chat_id' in answer:
            say("Команда из конференции ({answer['chat_id']}) > {answer['body']}")
        elif 'user_id' in answer:
            say("Команда из ЛС (id{answer['user_id']}) > {answer['body']}")

        try:
            self.plugin_system.call_command(command, self.vk, answer, arguments)
        except:
            self.vk.respond(answer, {
                "message": fmt(
                    "{self.vk.anti_flood()}. Произошла ошибка при выполнении команды <{command}>, "
                    "пожалуйста, сообщите об этом разработчику!")
            })

            say(
                "Произошла ошибка при вызове команды '{command}'. "
                "Сообщение: '{answer['body']}' с параметрами {arguments}. "
                "Ошибка:\n{traceback.format_exc()}",
                style='red')
            # print(message, command, arguments) -> for debug only


if __name__ == '__main__':
    bot = Bot()
