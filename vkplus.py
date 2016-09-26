# -*- coding: utf-8 -*-
# Класс с некоторыми доп. методами 

import vk_api

import random, string, errno
from requests.exceptions import ConnectionError

from say import say

class VkPlus:
    api = None

    def __init__(self, access_token, app_id=-1):
        try:
            if app_id == -1:
                self.api = vk_api.VkApi(token=access_token)
            else:
                self.api = vk_api.VkApi(app_id, token=access_token)

            self.api.authorization()  # Авторизируемся
        except vk_api.AuthorizationError as error_msg:
            print(error_msg)
            exit()

    # values передаются все, кроме user_id/chat_id
    # Поэтому метод и называется respond, ваш кэп
    # Сделано для упрощения ответа. В пагине или другом коде 
    # не нужно "думать" о том, откуда пришло сообщение:
    # из диалога, или из беседы (чата, конференции).

    def method(self, key, data=None):
        try:
            return self.api.method(key, data)
        except ConnectionError as e:
            if e.errno != errno.ECONNRESET:
                print('Exeption at vkservice:')
                print(e.message)
        except vk_api.vk_api.ApiError as error:
            say("Ошибка при вызове метода API {key} с значениями {data}.", style = 'red')

    def respond(self, to, values):
        flood_bypass_message = 'Обход анти-флуд системы'
        try:
            if 'chat_id' in to:  # если это беседа
                values['chat_id'] = to['chat_id']
                self.method('messages.send', values)
            else:  # если ЛС
                values['user_id'] = to['user_id']
                self.method('messages.send', values)
        except vk_api.vk_api.ApiError as err:
            if err.code == 9:
                if 'message' in values:
                    print(('Respond has api error with code ' + str(err.code) + '. Try to detour.'))
                    values['message'] += '\n {(random.choice(string.ascii_uppercase + string.digits) for _ in range(5))}'
                    try:
                        self.api.method('messages.send', values)
                    except vk_api.vk_api.ApiError as err2:
                        if err2.code == 9:
                            print('Обход анти-флуда API не удался =(')
                        else:
                            print('Обход анти-флуда API не удался =( При обходе возникла ошибка\n: ' + str(err2.code))
                    else:
                        print('Обход анти-флуда API успешен.')
            else:
                print('Ошибка API в методе respond с кодом {err.code}')

    def mark_as_read(self, message_ids):
        values = {
            'message_ids': message_ids
        }
        self.method('messages.markAsRead', values)
