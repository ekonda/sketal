from os.path import abspath, isfile
import shutil
import asyncio

import hues
from plugin_system import PluginSystem
from vkplus import VkPlus
from command import CommandSystem


class Bot(object):
    '''Главный класс бота, создан для упрощённой работы с переменными'''

    def __init__(self):
        # По умолчанию все сообщения будут жирные и синие :)

        self.last_message_id = 0
        self.init_settings()
        self.vk_init()
        self.plugin_init()
        asyncio.sleep(0.25)  # успеть всё инициализировать

    def init_settings(self):
        '''Функция инициализации файла настроек и его создания'''
        # Если у нас есть только settings.py.sample
        if isfile('settings.py.sample') and not isfile('settings.py'):
            try:
                shutil.copy('settings.py.sample', 'settings.py')
            except:
                hues.error('У меня нет прав писать в текущую директорию, '
                           'проверьте ваши права на неё!')
                exit()
            hues.warn('Был создан файл settings.py, пожалуйста, измените значения на Ваши!')
            exit()
        # Если у нас уже есть settings.py
        elif isfile('settings.py'):
            import settings
            try:
                self.BLACKLIST = settings.blacklist
                self.PREFIXES = settings.prefixes
                self.log_messages = settings.log_messages
                if settings.vk_access_token:
                    self.is_token = True
                    self.token = settings.vk_access_token
                elif settings.vk_login and settings.vk_password:
                    self.is_token = False
                    self.vk_login = settings.vk_login
                    self.vk_password = settings.vk_password
                else:
                    hues.error('Проверьте, что у вас заполнены vk_login и vk_password, или vk_access_token!'
                               '\nБез них бот работать НЕ СМОЖЕТ.')
                    exit()
            except (ValueError, IndexError, AttributeError, NameError):
                hues.error('Проверьте содержимое файла settings.py, возможно вы удалили что-то нужное!')
                exit()
        # Если не нашли ни settings.py, ни settings.py.sample
        else:
            hues.error('settings.py и settings.py.sample не найдены, возможно вы их удалили?')
            exit()

    def vk_init(self):
        # Авторизуемся в ВК
        hues.warn('Авторизация в вк...')

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
        hues.success('Успешная авторизация')

    def plugin_init(self):
        # Подгружаем плагины
        hues.warn("Загрузка плагинов...")
        self.plugin_system = PluginSystem(folder=abspath('plugins'))
        self.plugin_system.register_commands()
        # Чтобы плагины могли получить список плагинов
        self.vk.get_plugins = self.plugin_system.get_plugins
        # Для парсинга команд с пробелом используется
        # обратная сортировка, для того, чтобы самые
        # длинные команды были первые в списке
        command_names = list(self.plugin_system.commands.keys())
        command_names.sort(key=len, reverse=True)
        self.cmd_system = CommandSystem(command_names, self.plugin_system)
        hues.success("Загрузка плагинов завершена")

    async def run(self):
        while True:
            await self.check_messages()

    async def check_messages(self):
        response = await self.vk.method('messages.get', self.ANSWER_VALUES)
        if response is not None and response['items']:
            self.last_message_id = response['items'][0]['id']
            for item in response['items']:
                # Если сообщение не прочитано и ID пользователя не в чёрном списке бота
                if item['read_state'] == 0 and item['user_id'] not in self.BLACKLIST:
                    await self.vk.mark_as_read(item['id'])
                    await self.check_if_command(item)

    async def check_if_command(self, answer):
        if self.log_messages:
            if 'chat_id' in answer:
                hues.info("Сообщение из конференции (#{answer['chat_id']}) > #{answer['body']}")
            elif 'user_id' in answer:
                hues.info("Сообщение из ЛС (id#{answer['user_id']}) > #{answer['body']}")
        await self.cmd_system.process_command(answer, self.vk)
        '''
        self.vk.respond(answer, {
            "message":
                "{self.vk.anti_flood()}. Произошла ошибка при выполнении команды <#{command}>, "
                "пожалуйста, сообщите об этом разработчику!"
        })

        error(
            "Произошла ошибка при вызове команды '#{command}'. "
            "Сообщение: '#{answer['body']}' с параметрами #{arguments}. "
            "Ошибка:\n#{traceback.format_exc()}",)
        # print(message, command, arguments) -> for debug only
        '''


if __name__ == '__main__':
    bot = Bot()
    hues.success('Приступаю к приему сообщений')
    loop = asyncio.get_event_loop()
    # запускаем бота
    loop.run_until_complete(bot.run())
