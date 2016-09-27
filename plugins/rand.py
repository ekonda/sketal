# -*- coding: utf-8 -*-

import random
from plugin_system import Plugin

plugin = Plugin('Рандом')


answers = []
answers.append('Вот ваше число:')


@plugin.on_command('рандом', 'ранд', 'random', 'rand', 'dice', 'кубик')
def call(vk, msg, args):
    try:
        if 2 < len(args) < 4:
            if args[2] < 0:
                num = random.randint(int(args[2]), 0)
            else:
                num = random.randint(0, int(args[2]))
        elif len(args) > 3:
            if int(args[2]) < int(args[3]):
                num = random.randint(int(args[2]), int(args[3]))
            else:
                num = random.randint(int(args[3]), int(args[2]))
        else:
            num = random.randint(1, 6)

        vk.respond(msg, {'message': str(num)})
    except (ValueError, ):
        vk.respond(msg, {'message': 'Хватить пихать ничисла 😥'})
        return
