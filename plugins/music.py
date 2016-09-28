import random
from plugin_system import Plugin

plugin = Plugin('Рекомендация музыки')

errors = []
errors.append('Открой аудио!')
errors.append('Аудиозаписи открой!')
errors.append('У тебя аудио закрыты!')
errors.append('Я бы с радостью тебе дал музыки, но у тебя закрыты аудиозаписи.')

answers = []
answers.append('Вот твоя музыка:')
answers.append('Вот, послушай.')
answers.append('Мои рекомендации для тебя:')
answers.append('Музыку заказывали?')
answers.append('Бесплатная музыка!')


@plugin.on_command('музыка', 'музыку', 'музон', 'музло')
def music_pro(vk, msg, args):
    music = None

    try:
        count = vk.method('audio.getRecommendations',
                          {'user_id': msg['user_id'], 'count': 1})

        music = vk.method('audio.getRecommendations',
                          {'user_id': msg['user_id'],
                           'offset': random.randint(0, count['count'] - 5),
                           'count': 5})
    except:
        print('Failed get music of id' + str(msg['user_id']))

    musicatt = []

    if music is not None and music['items']:
        for attach in music['items']:
            user = attach['owner_id']
            ident = attach['id']
            musicatt.append('audio' + str(user) + '_' + str(ident))

    attstring = ''

    if musicatt is not None:
        for item in musicatt:
            attstring += item + ','

    if attstring == '':
        vk.respond(msg, {'message': random.choice(errors)})
    else:
        vk.respond(msg, {'message': random.choice(answers),
                         'attachment': attstring})
