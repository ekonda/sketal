import random
from plugin_system import Plugin

plugin = Plugin('Рандом')


@plugin.on_command('рандом', 'случайно', 'кубик')
async def call(msg, args):
    try:
        # Если у нас два аргумента - это диапазон
        if len(args) == 2:
            if int(args[1]) < 0:
                num = random.randint(int(args[1]), 0)
            else:
                num = random.randint(0, int(args[1]))
        # Если один аргумент, то диапазон будет - (1, число)
        elif len(args) == 1:
            num = random.randint(1, int(args[0]))
        # Если нет аргументов, будем как кубик
        else:
            num = random.randint(1, 6)

        await msg.answer("Вот ваше число: " + str(num))
    except ValueError:
        return
