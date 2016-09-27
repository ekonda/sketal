
import random


class Plugin:
    vk = None

    plugin_type = 'command'

    def __init__(self, vk):
        self.vk = vk
        print('Случайные сиськи')

    def getkeys(self):
        keys = ['сиськи', 'boobs']
        ret = {}
        for key in keys:
            ret[key] = self
        return ret

    def call(self, msg):
        answers = []
        answers.append("Сиськи поданы!")
        answers.append("Случайные сиськи!")
        answers.append("Знакомься, сиськи")

        isphoto = False
        boobs = None

        while isphoto is False:
            values = {
                # owner_id = ид группы
                'owner_id': -20282193,
                'offset': random.randint(1, 500),
                'count': 1
            }

            boobs = self.vk.method('wall.get', values)
            if 'attachments' in boobs['items'][0]:
                if 'photo' in boobs['items'][0]['attachments'][0]:
                    isphoto = True

        boobs_att = boobs['items'][0]['attachments'][0]['photo']

        owner_id = str(boobs_att['owner_id'])
        att_id = str(boobs_att['id'])
        access_key = str(boobs_att['access_key'])

        attachment = 'photo' + owner_id + '_' + att_id + '_' + access_key

        print(attachment)

        self.vk.respond(msg, {'message': random.choice(answers),
                              'attachment': attachment})
