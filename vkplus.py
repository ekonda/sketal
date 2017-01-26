# Standart library
import json
import random
import string
# PyPI
import asyncio
import hues
import aiovk
from aiovk.drivers import HttpDriver
from aiovk.mixins import LimitRateDriverMixin

# Custom
from utils import fatal


class FloodError(Exception):
    pass


class NotHavePerms(Exception):
    pass


# Driver for 3 requests per sec limitation (actually 1.2 sec)
class RatedDriver(LimitRateDriverMixin, HttpDriver):
    requests_per_period = 1
    period = 0.4


class VkPlus(object):
    api = None

    def __init__(self, token=None, login=None, password=None, app_id=5668099, scope=140492191):

        self.group_methods = ('groups.getById', 'groups.getMembers', 'execute')

        self.is_token = token
        self.login = login
        self.password = password
        self.appid = app_id
        self.scope = scope
        self.init_vk()

    def init_vk(self):
        if self.is_token:
            self.api_session = aiovk.TokenSession(access_token=self.is_token, driver=RatedDriver())
        elif self.login and self.password:
            self.login = self.login
            self.password = self.password
            self.api_session = aiovk.ImplicitSession(self.login, self.password, self.appid,
                                                     scope=self.scope, driver=RatedDriver())  # all scopes
        else:
            fatal('Вы попытались инициализировать объект класса VkPlus без данных для авторизации!')
        self.api = aiovk.API(self.api_session)

        # Паблик API используется для методов, которые не нуждаются в регистрации (users.get и т.д)
        # Используется только при access_token вместо аккаунта
        if self.is_token:
            self.public_api_session = aiovk.TokenSession(driver=RatedDriver())
            self.public_api = aiovk.API(self.public_api_session)

    async def method(self, key: str, data: dict={}):
        # Если у нас token, то для всех остальных методов
        # кроме разрешённых вызовем паблик API
        if key not in self.group_methods and self.is_token and 'message' not in key:
            api_method = self.public_api
        else:
            api_method = self.api
        try:
            return await api_method(key, **data) if data else await api_method(key)
        except (asyncio.TimeoutError, json.decoder.JSONDecodeError):
            return await api_method(key, **data) if data else await api_method(key)
        except aiovk.exceptions.VkAuthError:
            message = 'TOKEN' if self.is_token else 'LOGIN и PASSWORD'
            fatal("Произошла ошибка при авторизации API, "
                  "проверьте значение {} в settings.py!".format(message))

        except (aiovk.exceptions.VkAPIError, aiovk.exceptions.VkCaptchaNeeded) as exc:
            if not hasattr(exc, 'error_code'):
                print("FUCKING CAPTCHA!")
                return {}
            if exc.error_code == 9:
                if 'message' not in data:
                    return
                # Анти-флуд (рандомные 5 символов)
                data['message'] += '\n Анти-флуд (API): {}'.format(self.anti_flood())
                try:
                    await self.method('messages.send', data)
                except aiovk.exceptions.VkAPIError:
                    hues.error('Обход анти-флуда API не удался =(')
            else:
                hues.error("Произошла ошибка при вызове метода API {k} "
                           "с значениями {d}:\n{e}".format(k=key, d=data, e=exc))
                # except Exception as exc:
                #   hues.error('Неизвестная ошибка: \n{}'.format(exc))

    @staticmethod
    def anti_flood():
        """Функция для обхода антифлуда API ВК"""
        return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(5))

    async def respond(self, values):
        """Функция для отправки сообщения и проверки на ошибки"""
        try:
            await self.method('messages.send', values)
        # Если мы послали слишком много одинаковых сообщений
        except FloodError:
            if 'message' not in values:
                return
            values['message'] += '\n Анти-флуд (API): {}'.format(self.anti_flood())
            try:
                await self.method('messages.send', values)
            except aiovk.exceptions.VkAPIError:
                hues.error('Обход анти-флуда API не удался =(')

    async def mark_as_read(self, message_ids):
        """Пометить сообщение(я) как прочитанное"""
        values = {
            'message_ids': message_ids
        }
        await self.method('messages.markAsRead', values)

    async def resolve_name(self, screen_name):
        """Функция для перевода короткого имени в числовой ID"""
        result = await self.method('utils.resolveScreenName', {'screen_name': screen_name})
        if result:
            return result['object_id']
        else:
            return None


class Message(object):
    """Класс, объект которого передаётся в плагин для упрощённого ответа"""

    def __init__(self, vk_api_object, answer_values: dict):
        self._values = answer_values
        self.vk = vk_api_object
        self.conf = False
        self.user = False
        if 'chat_id' in answer_values:
            self.conf = True
            self.cid = int(answer_values['chat_id'])

        elif 'user_id' in answer_values:
            self.user = True
            self.uid = int(answer_values['user_id'])
        else:
            raise ValueError('answer_values dict must contain chat_id or user_id')
        self.id = answer_values['uid']
        self.body = answer_values['body']
        self.timestamp = answer_values['date']

        # Словарь для отправки к ВК при ответе
        if self.conf:
            self.answer_values = {'chat_id': self.cid}
        elif self.user:
            self.answer_values = {'user_id': self.uid}

    async def answer(self, msg, **additional_values):
        """Функция ответа для упрощения создания плагинов. Так же может принимать доп.параметры"""
        if additional_values is None:
            additional_values = dict()
        values = dict(**self.answer_values, message=msg, **additional_values)
        await self.vk.respond(values)
