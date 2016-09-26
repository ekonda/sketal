# -*- coding: utf-8 -*-

import time
import builtins
from os.path import abspath

from say import say, fmt

from plugin_system import PluginSystem
from vkplus import VkPlus
import settings

global vk

builtins.print = say  # Переопределить print функцией say (совместима с print)


def good(string):  # Функция для упрощённого вывода зелёных сообщений
    say(string, style='green')


def main():
    BLACKLIST = settings.blacklist

    global lastmessid
    lastmessid = 0
    say('Авторизация в вк...', style='yellow')
    global vk
    vk = VkPlus(settings.vk_access_token, settings.vk_app_id)
    good('Успешная авторизация')

    say.title("Загрузка плагинов:")

    # Подгружаем плагины
    global plugin_system
    plugin_system = PluginSystem(folder=abspath('plugins'))
    plugin_system.register_events()
    say.title("Загрузка плагинов завершена")

    good('Приступаю к приему сообщений')

    while True:

        values = {
            'out': 0,
            'offset': 0,
            'count': 20,
            'time_offset': 50,
            'filters': 0,
            'preview_length': 0,
            'last_message_id': lastmessid
        }

        response = vk.method('messages.get', values)
        if response is not None and response['items']:
            lastmessid = response['items'][0]['id']
            for item in response['items']:
                if item['read_state'] == 0 and item['user_id'] not in BLACKLIST:
                    execute_command(item)
                    # plugin_system.call_event(ite)
                    vk.mark_as_read(item['id'])  # Помечаем прочитанным

        time.sleep(0.1)


def execute_command(message):
    if not message['body']:  # Если строка пустая
        return
    words = message['body'].split()
    prefix = words[0].lower()

    prefixes = settings.prefixes

    if prefix in prefixes:
        if len(words) > 1:  # Если есть команда (может и аргументы)
            command = words[1].lower()
            arguments = words[2:]
            if 'chat_id' in message:
                say("Команда из конференции ({message['chat_id']}) > {message['body']}", style='blue+bold')
            elif 'user_id' in message:
                say("Команда из ЛС (id{message['user_id']}) > {message['body']}", style='blue+bold')
            try:
                plugin_system.call_event(command, vk, message, arguments)
            except:
                vk.respond(message, {
                    "message": fmt(
                        "{vk.anti_flood()}. Произошла ошибка при выполнении команды <{command}>, пожалуйста, сообщите об этом разработчику!")
                })

                say(
                    "Произошла ошибка при вызове команды '{command}'. Сообщение: '{message['body']}' с параметрами {arguments}. "
                    "Ошибка:\n{traceback.format_exc()}",
                    style='red')
            print(message, words[1].lower(), words[2:])


if __name__ == '__main__':
    main()
