import random
from plugin_system import Plugin

plugin = Plugin('Случайные мемы')

answers = '''Мемы поданы!
Классный мемес!
Знакомься, мемасик
'''.splitlines()


@plugin.on_command('мемы', 'мемасики', 'мем', 'мемчики', 'мемасик', 'мемосы', 'дай мемасы')
async def call(msg, args):
    isphoto = False
    boobs = None

    while isphoto is False:
        values = {
            # owner_id = ид группы
            'owner_id': -87960594,
            'offset': random.randint(1, 1985),
            'count': 1
        }

        boobs = await msg.vk.method('wall.get', values)
        if 'attachments' in boobs['items'][0]:
            if 'photo' in boobs['items'][0]['attachments'][0]:
                isphoto = True

    boobs_att = boobs['items'][0]['attachments'][0]['photo']

    owner_id = str(boobs_att['owner_id'])
    att_id = str(boobs_att['id'])
    access_key = str(boobs_att['access_key'])

    attachment = 'photo' + owner_id + '_' + att_id + '_' + access_key

    await msg.answer(random.choice(answers), attachment=attachment)
