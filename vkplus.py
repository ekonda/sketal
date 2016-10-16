import random
import string
from time import time

import asyncio
import hues
import aiovk

from utils import fatal

class FloodError(Exception): pass


class NotHavePerms(Exception): pass


class VkPlus(object):
    api = None

    def __init__(self, token=None, login=None, password=None):

        self.group_methods = ('groups.getById', 'groups.getMembers', 'execute')

        self.is_token = token
        self.login = login
        self.password = password
        self.init_vk()

    def init_vk(self):
        if self.is_token:
            self.api = aiovk.TokenSession(access_token=self.is_token)
        elif self.login and self.password:
            self.login = self.login
            self.password = self.password
            self.api = aiovk.ImplicitSession(self.login, self.password, 5668099,
                                             scope=140489887)  # all scopes
        else:
            fatal('Вы попытались инициализировать объект класса VkPlus без данных для авторизации!')
        self._api = aiovk.API(self.api)
        self._q = asyncio.Queue()
        self.last_time = 0
        asyncio.ensure_future(self.dispatcher())

        # Паблик API используется для методов, которые не нуждаются в регистрации (users.get и т.д)
        # Используется только при access_token вместо аккаунта
        if self.is_token:
            self.public_api = aiovk.API(aiovk.TokenSession())

    # Если нас вызывают
    async def __call__(self, *args, **kwargs):
        fut = asyncio.Future()
        coro = self._api(*args, **kwargs)
        await self._q.put((coro, fut))
        return await fut

    # Функция, которая ограничивает кол-во запросов до 3 в секунду
    async def dispatcher(self):
        c = 0
        while True:
            coro, fut = await self._q.get()
            if c >= 3:
                if time() - self.last_time <= 1:
                    await asyncio.sleep(1.1)
                c = 0
            r = await coro
            fut.set_result(r)
            self.last_time = time()
            c += 1

    async def method(self, key, data=None):
        # Если у нас token, то для всех остальных методов
        # кроме разрешённых вызовем паблик API
        if key not in self.group_methods and self.is_token and 'message' not in key:
            api_method = self.public_api
        else:
            api_method = self
        try:
            return await api_method(key, **data) if data else await api_method(key)

        except aiovk.exceptions.VkAuthError as exc:
            if not str(exc) == 'User authorization failed':
                raise NotHavePerms
            message = 'access_token' if self.is_token else 'vk_login и vk_password'
            fatal("Произошла ошибка при авторизации API, "
                  "проверьте значение {} в settings.py!".format(message))

        except (aiovk.exceptions.VkAPIError, NotHavePerms) as exc:
            if exc.error_code == 9:
                raise FloodError
            else:
                hues.error("Произошла ошибка при вызове метода API {k} "
                           "с значениями {d}:\n{e}".format(k=key, d=data, e=exc))
                # except Exception as exc:
                #   hues.error('Неизвестная ошибка: \n{}'.format(exc))

    def anti_flood(self):
        '''Функция для обхода антифлуда API ВК'''
        return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(5))

    # values передаются все, кроме user_id/chat_id
    # Сделано для упрощения ответа. В пагине или другом коде
    # не нужно "думать" о том, откуда пришло сообщение:
    # из диалога, или из беседы (чата, конференции).
    async def respond(self, to, values):
        try:
            if 'chat_id' in to:  # если это беседа
                values['chat_id'] = to['chat_id']
                await self.method('messages.send', values)
            else:  # если ЛС
                values['user_id'] = to['user_id']
                await self.method('messages.send', values)
        # Эта ошибка будет поймана только если ошибка - слишком много запросов в секунду
        except FloodError:
            if not 'message' in values:
                return
            values['message'] += '\n Анти-флуд (API): {}'.format(self.anti_flood())
            try:
                await self.method('messages.send', values)
            except aiovk.exceptions.VkAPIError:
                hues.error('Обход анти-флуда API не удался =(')

    async def mark_as_read(self, message_ids):
        values = {
            'message_ids': message_ids
        }
        await self.method('messages.markAsRead', values)
