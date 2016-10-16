# Standart library
import random
import string

# PyPI
import hues
import aiovk
from aiovk.drivers import HttpDriver
from aiovk.mixins import LimitRateDriverMixin

# Custom
from utils import fatal

class FloodError(Exception): pass


class NotHavePerms(Exception): pass


# Driver for 3 requests per sec limitation
class RatedDriver(LimitRateDriverMixin, HttpDriver):
    requests_per_period = 3
    period = 1.15

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
            self.api = aiovk.TokenSession(access_token=self.is_token, driver=RatedDriver())
        elif self.login and self.password:
            self.login = self.login
            self.password = self.password
            self.api = aiovk.ImplicitSession(self.login, self.password, 5668099,
                                             scope=140489887, driver=RatedDriver())  # all scopes
        else:
            fatal('Вы попытались инициализировать объект класса VkPlus без данных для авторизации!')
        self.api = aiovk.API(self.api)

        # Паблик API используется для методов, которые не нуждаются в регистрации (users.get и т.д)
        # Используется только при access_token вместо аккаунта
        if self.is_token:
            self.public_api = aiovk.API(aiovk.TokenSession())

    async def method(self, key, data=None):
        # Если у нас token, то для всех остальных методов
        # кроме разрешённых вызовем паблик API
        if key not in self.group_methods and self.is_token and 'message' not in key:
            api_method = self.public_api
        else:
            api_method = self.api
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
