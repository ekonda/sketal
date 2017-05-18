import random

# plugin = Plugin('Рекомендация музыки')

errors = ['Открой аудио!', 'Аудиозаписи открой!', 'У тебя аудио закрыты!',
          'Я бы с радостью тебе дал музыки, но у тебя закрыты аудиозаписи.']

answers = ['Вот твоя музыка:', 'Вот, послушай.', 'Мои рекомендации для тебя:', 'Музыку заказывали?',
           'Бесплатная музыка!']


# Плагин сломан в данный момент :(
# @plugin.on_command('музыка', 'музыку', 'музон', 'музло')
async def music_pro(msg, args):
    music = None
    try:
        music = await msg.vk.method('audio.getRecommendations',
                                    {'user_id': msg.user_id, 'shuffle': 1})
    except Exception as ex:
        print(ex)
        print('Failed get music of id' + str(msg.user_id))

    musicatt = []
    print(music)
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
