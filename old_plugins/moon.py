import random


class Plugin:
    vk = None

    plugin_type = 'command'

    def __init__(self, vk):
        self.vk = vk
        print('Луна')

    def getkeys(self):
        keys = ['луна', '&#127770;', '??']
        ret = {}
        for key in keys:
            ret[key] = self
        return ret

    def call(self, msg):
        answers = []

        answers.append('&#127770;')
        answers.append('&#127770;&#127770;')

        self.vk.respond(msg, {'message': random.choice(answers)})
