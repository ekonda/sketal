import random
from plugin_system import Plugin

plugin = Plugin('Рекомендация музыки')

errors = ['Открой аудио!', 'Аудиозаписи открой!', 'У тебя аудио закрыты!',
          'Я бы с радостью тебе дал музыки, но у тебя закрыты аудиозаписи.']

answers = ['Вот твоя музыка:', 'Вот, послушай.', 'Мои рекомендации для тебя:', 'Музыку заказывали?',
           'Бесплатная музыка!']


@plugin.on_command('музыка', 'музыку', 'музон', 'музло')
async def music_pro(msg, args):
    music = None

    try:
        count = await msg.vk.method('audio.getRecommendations',
                                    {'user_id': msg['user_id'], 'count': 1})

        music = await msg.vk.method('audio.getRecommendations',
                                    {'user_id': msg['user_id'],
                                     'offset': random.randint(0, count['count'] - 5),
                                     'count': 5})
    except Exception:
        print('Failed get music of id' + str(msg.id))

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
        await msg.answer(random.choice(errors))
    else:
        await msg.answer(random.choice(answers), attachment=attstring)
