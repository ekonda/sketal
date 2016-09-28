import random
from plugin_system import Plugin

plugin = Plugin("Случайное с двача")

answers = []
answers.append("Каеф")
answers.append("Не баян (баян)")
answers.append("Ну держи!")
answers.append("🌚")


@plugin.on_command('двач', '2ch', 'двачик', 'мемы с двача')
def get_memes(vk, msg, args):
    isphoto = False
    boobs = None

    while isphoto is False:
        values = {
            # owner_id = ид группы
            'owner_id': -22751485,
            'offset': random.randint(1, 1985),
            'count': 1
        }

        boobs = vk.method('wall.get', values)
        if 'attachments' in boobs['items'][0]:
            if 'photo' in boobs['items'][0]['attachments'][0]:
                isphoto = True

    boobs_att = boobs['items'][0]['attachments'][0]['photo']

    owner_id = str(boobs_att['owner_id'])
    att_id = str(boobs_att['id'])
    access_key = str(boobs_att['access_key'])

    attachment = 'photo' + owner_id + '_' + att_id + '_' + access_key

    vk.respond(msg, {'message': random.choice(answers),
                     'attachment': attachment})
