import random
from plugin_system import Plugin

answers = []

answers.append('🌚')
answers.append('🌚🌚')

plugin = Plugin('Луна')


@plugin.on_command('луна', '🌚')
def get_moon(vk, msg, args):
    vk.respond(msg, {'message': random.choice(answers)})
