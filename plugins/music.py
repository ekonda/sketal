import random
from plugin_system import Plugin

plugin = Plugin('Рекомендация музыки')

errors = ['Открой аудио!', 'Аудиозаписи открой!', 'У тебя аудио закрыты!',
          'Я бы с радостью тебе дал музыки, но у тебя закрыты аудиозаписи.']

answers = ['Вот твоя музыка:', 'Вот, послушай.', 'Мои рекомендации для тебя:', 'Музыку заказывали?',
           'Бесплатная музыка!']


@plugin.on_command('музыка', 'музыку', 'музон', 'музло')
async def music_pro(vk, msg, args):
    music = None

    try:
        count = await vk.method('audio.getRecommendations',
                                {'user_id': msg['user_id'], 'count': 1})

        music = await vk.method('audio.getRecommendations',
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
        await vk.respond(msg, {'message': random.choice(errors)})
    else:
        await vk.respond(msg, {'message': random.choice(answers),
                               'attachment': attstring})
