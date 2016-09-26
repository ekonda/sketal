# -*- coding: utf-8 -*-

import os
import sys
import time
import builtins
from say import say
from vkplus import VkPlus
import traceback
import settings

global vk

builtins.print = say  # Переопределить print функцией say (совместима с print)


def good(string): # Функция для упрощённого вывода зелёных сообщений
    say(string, style='green')


def main():
    try:
        BLACKLIST = settings.blacklist
    except:
        BLACKLIST = (0, 0)

    try:
        path = settings.path
    except:
        path = 'plugins/'

    global cmds
    cmds = {}
    plugins = {}

    global lastmessid
    lastmessid = 0

    say('Авторизация в вк...', style='yellow')
    global vk
    vk = VkPlus(settings.vk_access_token, settings.vk_app_id)
    good('Успешная авторизация')

    say.title("Загрузка плагинов:")

    # Подгружаем плагины
    sys.path.insert(0, path)
    for f in os.listdir(path):
        fname, ext = os.path.splitext(f)
        if ext == '.py':
            mod = __import__(fname)
            plugins[fname] = mod.Plugin(vk)
    sys.path.pop(0)

    say.title("Загрузка плагинов завершена")

    # Регистрируем плагины
    for plugin in list(plugins.values()):
        for key, value in list(plugin.getkeys().items()):
            cmds[key] = value

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
                    command(item, cmds)
                    vk.mark_as_read(item['id'])  # Помечаем прочитанным

        time.sleep(0.1)


def command(message, cmds):
    if message['body'] == '':
        return
    words = message['body'].split()

    try:
        prefixes = settings.prefixes
    except:
        prefixes = ['lolbot', 'лолбот', 'лб', 'lb', 'фб', 'файнбот', 'fb', 'finebot']

    if words[0].lower() in prefixes:
        if 'chat_id' in message:
            say("Команда из конференции ({message['chat_id']}) > {message['body']}", style='blue+bold')
        elif 'user_id' in message:
            say("Команда из ЛС (id{message['user_id']}) > {message['body']}", style='blue+bold')
        if len(words) > 1 and words[1] in cmds:
            command_execute(message, words[1].lower(), words[2:])


def command_execute(message, plugin, params):
    global vk
    if plugin and plugin in cmds:
        # Помечаем прочитанным перед выполнением команды.           
        vk.mark_as_read(message['id'])

        # Приоритеты аргументов:
        # 0. message - всегда есть.
        # 1. params, with_args, args

        # 0
        args = [message]

        # 1
        if any(s in cmds[plugin].plugin_type for s in ['params', 'with_args', 'args']):
            args.append(params)
        # 2 
        if 'settings' in cmds[plugin].plugin_type:
            args.append(settings)
        try:
            cmds[plugin].call(*args)
        except Exception as error:
            say(
                "Произошла ошибка в плагине {plugin} при вызове команды {message['body']} с параметрами {params}. "
                "Ошибка:\n{traceback.format_exc()}",
                style='red')
        return True
    else:
        return False


if __name__ == '__main__':
    main()
