import random


class Plugin:
    vk = None

    plugin_type = 'command'

    def __init__(self, vk):
        self.vk = vk
        print('Плагин музыки')

    def getkeys(self):
        keys = ['музыка', 'музыку', 'music']
        ret = {}
        for key in keys:
            ret[key] = self
        return ret

    def call(self, msg):
        music = None

        errors = []
        errors.append('Открой аудио, мудак!')
        errors.append('Мудак, аудиозаписи открой!')
        errors.append('У тебя аудио закрыты, мудак!')
        errors.append('Я бы с радостью тебе дал музыки, но ты мудак.')

        try:
            count = self.vk.method('audio.getRecommendations',
                                   {'user_id': msg['user_id'], 'count': 1})

            music = self.vk.method('audio.getRecommendations',
                                   {'user_id': msg['user_id'],
                                    'offset': random.randint(0, count['count'] - 5),
                                    'count': 5})
        except:
            print(('Failed get music of id' + str(msg['user_id'])))

        musicatt = []

        if music is not None and music['items']:
            for attach in music['items']:
                user = attach['owner_id']
                ident = attach['id']
                musicatt.append('audio' + str(user) + '_' + str(ident))

        answers = []
        answers.append('Вот твоя музыка:')
        answers.append('Вот, послушай.')
        answers.append('Мои рекомендации для тебя:')
        answers.append('Музыку заказывали?')
        answers.append('Бесплатная музыка!')

        attstring = ''

        if musicatt is not None:
            for item in musicatt:
                attstring += item + ','

        if attstring == '':
            self.vk.respond(msg, {'message': random.choice(errors)})
        else:
            self.vk.respond(msg, {'message': random.choice(answers),
                                  'attachment': attstring})
