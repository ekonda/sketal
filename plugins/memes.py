import random
from plugin_system import Plugin

plugin = Plugin('Случайные мемы',
                usage='мемы - показать случайный мем')

answers = '''Мемы поданы!
Классный мемес!
Знакомься, мемасик
'''.splitlines()


@plugin.on_command('мемы', 'мемасики', 'мем', 'мемчики', 'мемасик', 'мемосы')
async def call(msg, args):
    photo = False
    data = None

    while not photo:
        values = {
            # owner_id = ид группы
            'owner_id': -129950840,
            'offset': random.randint(1, 400),
            'count': 5
        }

        data = await msg.vk.method('wall.get', values)
        data = data['items'][0]
        if 'attachments' in data:
            if 'photo' in data['attachments'][0]:
                photo = True

    attrs = data['attachments'][0]['photo']

    owner_id, att_id, key = attrs['owner_id'], attrs['id'], attrs['access_key']

    attachment = f'photo{owner_id}_{att_id}_{key}'

    await msg.answer(random.choice(answers), attachment=attachment)
