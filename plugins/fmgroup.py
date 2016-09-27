import random
from plugin_system import Plugin

plugin = Plugin('Записи файнмайн')

answers = []
answers.append("Куйня какая-то!")
answers.append("Великолепно (Нет)")
answers.append("Я сам смотреть не буду, но вы смотрите.")

@plugin.on_command('фмзаписи', 'записи_файнмайн')
def call(vk, msg, args):

    isphoto = False
    boobs = None

    while isphoto is False:
        values = {
            # owner_id = ид группы
            'owner_id': -35140461,
            'offset': random.randint(1, 1000),
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

    print(attachment)

    vk.respond(msg, {'message': random.choice(answers),
                          'attachment': attachment})
