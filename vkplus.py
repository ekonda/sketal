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
        answ_flood_detour = [u'Flood detour', u'Обход ошибки о флуде']
        
        if 'chat_id' in to:
            values['chat_id'] = to['chat_id']
            self.method('messages.send', values)
        else:
            values['user_id'] = to['user_id']
            self.method('messages.send', values)
        try:
            self.method('messages.send', values)
        except vk_api.vk_api.ApiError, err:
            if err.code == 9:
                if values.has_key('message'):
                    print(u'Respond has api error with code '+ str(err.code) + u'. Try to detour.')
                    values['message'] += u'\n' + random.choice(answ_flood_detour) + u'. ' + ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits + string.lowercase) for _ in range(random.randint(5, 15)))
                    try:
                        self.api.method('messages.send', values)
                    except vk_api.vk_api.ApiError, err2:
                        if err2.code == 9:
                            print(u'Detour of flood control failed =(')
                        else:
                            print(u'Detour of flood control failed =( But another error: '+str(err2.code))
                    else:
                        print(u'Detour of flood control success. F*ck you VK.')
                else:
                    print(u'Respond has api error with code '+ str(err.code))


    def markasread(self, id):
        values = {
            'message_ids': id
        }
        self.method('messages.markAsRead', values)
