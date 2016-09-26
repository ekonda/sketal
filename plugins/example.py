# -*- coding: utf-8 -*-
from say import fmt

from plugin_system import Plugin

plugin = Plugin("Пример плагина")

@plugin.on_command('примерплагина', 'тестовыйплагин')
def anynameoffunctioncanbehere(vk, raw_message, args):
    print("OK!")
    vk.respond(raw_message, {'message': fmt('Пример плагина (аргументы - {args})')})
