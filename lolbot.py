# -*- coding: utf-8 -*-

import time
import builtins
from os.path import abspath
import traceback  # используется в say()
from say import say, fmt

from plugin_system import PluginSystem
from vkplus import VkPlus
import settings

builtins.print = say  # Переопределить print функцией say (совместима с print)


def good(string):  # Функция для упрощённого вывода зелёных сообщений
    say(string, style='green')


class Bot(object):
    def __init__(self):
        self.BLACKLIST = settings.blacklist
        self.PREFIXES = settings.prefixes
        self.last_message_id = 0
        self.vk_init()
        self.plugin_init()
        good('Приступаю к приему сообщений')

        self.run()

    def vk_init(self):
        # Авторизуемся в ВК
        say('Авторизация в вк...', style='yellow')
        self.vk = VkPlus(settings.vk_access_token, settings.vk_app_id)
        good('Успешная авторизация')

    def plugin_init(self):
        # Подгружаем плагины
        say.title("Загрузка плагинов:")
        self.plugin_system = PluginSystem(folder=abspath('plugins'))
        self.plugin_system.register_events()
        # Чтобы плагины могли получить список команд
        self.vk.get_commands = self.plugin_system.get_commands
        say.title("Загрузка плагинов завершена")

    def run(self):
        while True:
            self.check_messages()

    def check_messages(self):

        values = {
            'out': 0,
            'offset': 0,
            'count': 20,
            'time_offset': 50,
            'filters': 0,
            'preview_length': 0,
            'last_message_id': self.last_message_id
        }

        response = self.vk.method('messages.get', values)
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
        prefix = words[0].lower()  # берём префикс - первое слово в нижнем регистре

        if prefix in self.PREFIXES:  # Если наш бот должен реагировать на этот префикс
            if len(words) > 1:  # Если есть команда (может и аргументы)
                command = words[1].lower()  # Получаем команду (и приводим в нижний регистр)
                arguments = words[2:]  # Получаем аргументы срезом
                if 'chat_id' in message:
                    say("Команда из конференции ({message['chat_id']}) > {message['body']}", style='blue+bold')
                elif 'user_id' in message:
                    say("Команда из ЛС (id{message['user_id']}) > {message['body']}", style='blue+bold')
                try:
                    self.plugin_system.call_event(command, self.vk, message, arguments)
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
