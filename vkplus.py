# -*- coding: utf-8 -*-
# Класс с некоторыми доп. методами 

import vk_api


class VkPlus:
    api = None

    def __init__(self, login, password, app_id=-1):
        try:
            if app_id == -1:
                self.api = vk_api.VkApi(login, password)  
            else:
                self.api = vk_api.VkApi(login, password, app_id)  

            self.api.authorization() # Авторизируемся
        except vk_api.AuthorizationError as error_msg:
            print(error_msg)
            return None

    # values передаются все, кроме user_id/chat_id
    # Поэтому метод и называется respond, ваш кэп
    def respond(self, to, values):
        if 'chat_id' in to:
            values['chat_id'] = to['chat_id']
            self.api.method('messages.send', values)
        else:
            values['user_id'] = to['user_id']
            self.api.method('messages.send', values)

    def markasread(self, id):
        values = {
            'message_ids': id
        }
        self.api.method('messages.markAsRead', values)
