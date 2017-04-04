import random

from plugin_system import Plugin
usage=['двач - случайная фотка с двача',
       'мемы - случайная фотка из https://vk.com/public129950840']

plugin = Plugin("Случайные посты из пабликов",
                usage=usage)

answers = ["Каеф", "Не баян (баян)", "Ну держи!", "🌚"]


async def give_memes(msg, group_id):
    """Получает фотографию из случайного поста выбранной группы"""
    photo = None

    values = {
        # owner_id = ид группы
        'owner_id': group_id,
        'offset': random.randint(1, 1985),
        'count': 1
    }

    # Пока мы не нашли фотографию
    while not photo:
        data = await msg.vk.method('wall.get', values)
        attaches = data['items'][0].get('attachments')
        if attaches:
            photo = attaches[0].get('photo')
        
        values['offset'] = random.randint(1, 1985)

    oid = photo['owner_id']
    att_id = photo['id']
    access_key = photo['access_key']

    attachment = f'photo{oid}_{att_id}_{access_key}'
    await msg.answer(random.choice(answers), attachment=attachment)


@plugin.on_command('двач', '2ch', 'двачик')
async def twoch_memes(msg, args):
    group_id = -22751485
    await give_memes(msg, group_id)


@plugin.on_command('мемы', 'мемасики', 'мем', 'мемчики', 'мемасик', 'мемосы')
async def just_memes(msg, args):
    group_id = -129950840
    await give_memes(msg, group_id)
