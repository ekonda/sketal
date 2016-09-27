# Класс с некоторыми доп. методами

import vk_api

import random, string, errno
from requests.exceptions import ConnectionError

from say import say, fmt


class VkPlus:
    api = None

    def __init__(self, token=None, login=None, password=None):

        self.group_methods = ('groups.getById', 'groups.getMembers', 'execute')

        self.is_token = token

        try:
            if token:
                self.api = vk_api.VkApi(token=token)
            elif login and password:
                self.login = login
                self.password = password
                self.api = vk_api.VkApi(login=login, password=password)
            else:
                say('Вы попытались инициализировать объект класса VkPlus без данных для авторизации!', style='red')
                exit()
            self.api.authorization()  # Авторизируемся
        # Если произошла ошибка при авторизации
        except vk_api.AuthorizationError as error_msg:
            print(error_msg)
            exit()

        # Паблик API используется для методов, которые не нуждаются в регистрации (users.get и т.д)
        # Используется только при access_token вместо аккаунта
        if self.is_token:
            self.public_api = vk_api.VkApi()
            self.public_api.authorization()

    def method(self, key, data=None):
        # Если у нас token, то для всех остальных методов
        # кроме разрешённых вызовем паблик API
        api_method = None

        if key not in self.group_methods and self.is_token and 'message' not in key:
            api_method = self.public_api.method
        else:
            api_method = self.api.method

        try:
            return api_method(key, data)
        except vk_api.vk_api.ApiError as error:
            if error.code == 9:
                raise
            if error.code == 5 and 'User authorization failed' in str(error):
                say("Произошла ошибка при авторизации API, "
                    "проверьте значение access_token в settings.py!", style='red')
                exit()
            else:
                say("Произошла ошибка при вызове метода {self.api_method} бота через API {key} с значениями {data}:\n{error}",
                    style='red')

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
            if not 'message' in values:
                return
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
