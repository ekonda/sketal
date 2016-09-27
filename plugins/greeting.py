import random
from plugin_system import Plugin

# Инициализируем возможные ответы
greetings = []
greetings.append('Слава Украине!')
greetings.append('Кекеке')
greetings.append('Запущен и готов служить!')
greetings.append('У контакта ужасный флуд-контроль, %username%')
greetings.append('Хуяк-хуяк и в продакшн')

plugin = Plugin('Приветствие')

@plugin.on_command('привет','приветствие', 'голос', 'ку')
def call(vk, msg, args):
    vk.respond(msg, {'message': random.choice(greetings)})
