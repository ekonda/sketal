# -*- coding: utf-8 -*-

import os
import sys
import time

from vkplus import VkPlus

import settings

global vk
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

    print('Авторизация в вк...')
    global vk
    vk = VkPlus(settings.vk_access_token, settings.vk_app_id)
    print('Успешная авторизация с аккаунтом')

    print('Подгружаем плагины...')

    print('---------------------------')

    # Подгружаем плагины
    sys.path.insert(0, path)
    for f in os.listdir(path):
        fname, ext = os.path.splitext(f)
        if ext == '.py':
            mod = __import__(fname)
            plugins[fname] = mod.Plugin(vk)
    sys.path.pop(0)

    print('---------------------------')

    # Регистрируем плагины
    for plugin in plugins.values():
        for key, value in plugin.getkeys().items():
            cmds[key] = value

    print('Приступаю к приему сообщений')

    while True:

        # обозначаем что аккаунт онлайн

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

        time.sleep(0.5)


def command(message, cmds):
    if message['body'] == u'':
        return
    words = message['body'].split()

    try:
        prefixes = settings.prefixes
    except:
        prefixes = ['lolbot', u'лолбот', u'лб', u'lb', u'фб', u'файнбот', u'fb', u'finebot']

    if words[0].lower() in prefixes:
        print('> ' + message['body']).encode('utf-8')
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

        cmds[plugin].call(*args)
        return True
    else:
        return False

if __name__ == '__main__':
    main()
