import random

from plugin_system import Plugin

# Инициализируем возможные ответы
greetings = ['🌚 Кекеке', 'Запущен и готов служить!']

plugin = Plugin('Приветствие',
                usage="привет - поприветствовать пользователя")


@plugin.on_command('привет', 'приветствие', 'голос', 'ку')
async def call(msg, args):
    await msg.answer(random.choice(greetings))
