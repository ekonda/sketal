import random
from plugin_system import Plugin

answers = ['🌚', '🌚🌚']

plugin = Plugin('Луна')


@plugin.on_command('луна', '🌚')
async def get_moon(vk, msg, args):
    await vk.respond(msg, {'message': random.choice(answers)})
