# Класс с некоторыми доп. методами

import vk_api

import random, string, errno
from requests.exceptions import ConnectionError

from say import say, fmt


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

    def method(self, key, data=None):
        try:
            return self.api.method(key, data)
        except ConnectionError as e:
            if e.errno != errno.ECONNRESET:
                print('Exeption at vkservice:')
                print(e)
        except vk_api.vk_api.ApiError as error:
            if error.code == 9:
                raise
            if error.code == 5 and 'User authorization failed' in str(error):
                say("Произошла ошибка при авторизации API, "
                    "проверьте значение access_token в settings.py!", style='red')
                exit()
            else:
                say("Произошла ошибка при вызове метода бота через API {key} с значениями {data}:\n{error}", style='red')

    def anti_flood(self):
        '''Функция для обхода антифлуда API ВК'''
        return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(5))

    # values передаются все, кроме user_id/chat_id
    # Сделано для упрощения ответа. В пагине или другом коде
    # не нужно "думать" о том, откуда пришло сообщение:
    # из диалога, или из беседы (чата, конференции).
    def respond(self, to, values):
        try:
            if 'chat_id' in to:  # если это беседа
                values['chat_id'] = to['chat_id']
                self.method('messages.send', values)
            else:  # если ЛС
                values['user_id'] = to['user_id']
                self.method('messages.send', values)
        # Эта ошибка будет поймана только если код ошибки равен 9 - см. def method()
        except vk_api.vk_api.ApiError:
            if 'message' in values:
                values['message'] += fmt('\n Анти-флуд (API): {self.anti_flood()}')
                try:
                    self.method('messages.send', values)
                except vk_api.vk_api.ApiError:
                    print('Обход анти-флуда API не удался =(')

    def mark_as_read(self, message_ids):
        values = {
            'message_ids': message_ids
        }
        self.method('messages.markAsRead', values)
