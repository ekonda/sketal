import random
from plugin_system import Plugin

plugin = Plugin('Записи файнмайн')

answers = '''Куйня какая-то!
Великолепно (Нет)
Я сам смотреть не буду, но вы смотрите.
'''.splitlines()


@plugin.on_command('фм записи', 'записи файнмайн')
async def call(msg, args):
    isphoto = False
    boobs = None

    while isphoto is False:
        values = {
            # owner_id = ид группы
            'owner_id': -35140461,
            'offset': random.randint(1, 1000),
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
