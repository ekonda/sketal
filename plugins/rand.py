import random
from plugin_system import Plugin

plugin = Plugin('Рандом')

@plugin.on_command('рандом', 'случайно', 'кубик')
def call(vk, msg, args):
    try:
        if len(args) == 2:
            if int(args[1]) < 0:
                num = random.randint(int(args[1]), 0)
            else:
                num = random.randint(0, int(args[1]))

        elif len(args) == 1:
            num = random.randint(1, int(args[0]))

        else:
            num = random.randint(1, 6)

        vk.respond(msg, {'message': "Вот ваше число: " + str(num)})
    except ValueError:
        return
