from plugin_system import Plugin

plugin = Plugin('Калькулятор')


@plugin.on_command('посчитай', 'сколько будет', 'калькулятор')
async def calc(msg, args):
    expression = ''.join(args)
    try:
        result = eval(expression)
    except:
        return await msg.answer('Мне не удалось посчитать!')
    await msg.answer('Я посчитал:\n' + str(result))
