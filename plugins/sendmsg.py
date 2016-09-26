# -*- coding: utf-8 -*-

import random


class Plugin:
    vk = None

    plugin_type = 'command args'

    def __init__(self, vk):
        self.vk = vk
        print('Написать анонимно')

    def getkeys(self):
        keys = ['send', 'написать', 'напиши', 'лс', 'msg']
        ret = {}
        for key in keys:
            ret[key] = self
        return ret

    def call(self, msg, args=None):

        if len(args) >= 2:
            if args[0].isdigit():
                uid = int(args[0])
                body = 'Меня тут попросили тебе написать: \n'
                for arg in args[1:]:
                    body = body + ' ' + arg.capitalize().encode('utf-8')
                val = {
                    # 'user_id':uid,
                    'peer_id': uid,
                    'message': body
                }
                self.vk.method('messages.send', val)
            else:
                self.vk.respond(msg, {'message': 'Не могу найти такой ID пользователя'})
        else:
            self.vk.respond(msg, {'message': 'Введи ID пользователя и сообщение для него'})
