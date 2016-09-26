# -*- coding: utf-8 -*-

import time
import builtins
from os.path import abspath

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
        self.lastmessid = 0
        say('Авторизация в вк...', style='yellow')
        self.vk = VkPlus(settings.vk_access_token, settings.vk_app_id)
        good('Успешная авторизация')

        # Подгружаем плагины
        say.title("Загрузка плагинов:")
        self.plugin_system = PluginSystem(folder=abspath('plugins'))
        self.plugin_system.register_events()
        say.title("Загрузка плагинов завершена")

        good('Приступаю к приему сообщений')

        self.run()
    def run(self):
        while True:
            values = {
                'out': 0,
                'offset': 0,
                'count': 20,
                'time_offset': 50,
                'filters': 0,
                'preview_length': 0,
                'last_message_id': self.lastmessid
            }

            response = self.vk.method('messages.get', values)
            if response is not None and response['items']:
                self.lastmessid = response['items'][0]['id']
                for item in response['items']:
                    if item['read_state'] == 0 and item['user_id'] not in self.BLACKLIST:
                        self.execute_command(item)
                        self.vk.mark_as_read(item['id'])  # Помечаем прочитанным

            time.sleep(0.1)

    def execute_command(self, message):
        if not message['body']:  # Если строка пустая
            return
        words = message['body'].split()  # Делим строку на список слов
        prefix = words[0].lower()

        if prefix in self.PREFIXES:
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
                            "{self.vk.anti_flood()}. Произошла ошибка при выполнении команды <{command}>, пожалуйста, сообщите об этом разработчику!")
                    })

                    say(
                        "Произошла ошибка при вызове команды '{command}'. Сообщение: '{message['body']}' с параметрами {arguments}. "
                        "Ошибка:\n{traceback.format_exc()}",
                        style='red')
                print(message, command, arguments)


if __name__ == '__main__':
    bot = Bot()
