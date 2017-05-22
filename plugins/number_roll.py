import random

from plugin_system import Plugin

usage = """рандом (от) (до) - случайное число в диапазоне (от, до)
Если нет "до", то диапазон (1, от). Если нет "от", то диапазон (1, 6)"""

plugin = Plugin('Рандом',
                usage=['рандом (от) (до) - случайное число в диапазоне (от, до)\n'
                       'Если нет "до", то диапазон (1, от). Если нет "от", то диапазон (1, 6)'])


@plugin.on_command('рандом', 'случайно', 'кубик')
async def call(msg, args):
    try:
        args = [int(arg) for arg in args]
    except ValueError:
        return await msg.answer("Один из аргументов - не число")

    # Если у нас два аргумента - это диапазон
    if len(args) == 2:
        start, end = args
        # Конечное значение больше начального
        if abs(end - start) > 0:
            num = random.randint(start, end)
        # Конечное число меньше начального
        else:
            num = random.randint(end, start)

    # Если один аргумент, то диапазон будет - (1, число)
    elif len(args) == 1:
        num = random.randint(1, args[0])
    # Если нет аргументов, то диапазон, как в игральном кубике
    else:
        num = random.randint(1, 6)

    await msg.answer("Моё число - " + str(num))
