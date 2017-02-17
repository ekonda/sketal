# Standart library
import json
import random
import string
# PyPI
import asyncio

import aiohttp
import hues
import aiovk
from aiovk.drivers import HttpDriver
from aiovk.mixins import LimitRateDriverMixin
try:
    from settings import CAPTCHA_KEY, CAPTCHA_SERVER
except:
    CAPTCHA_SERVER = ""
    CAPTCHA_KEY = ""
# Custom
from utils import fatal, MessageEventData, chunks

from captcha_solver import CaptchaSolver

if CAPTCHA_KEY and CAPTCHA_SERVER:
    solver = CaptchaSolver(CAPTCHA_SERVER, api_key=CAPTCHA_KEY)
else:
    solver = None


class NoPermissions(Exception):
    pass


# Драйвер для ограничения запросов к API - 3 раза в секунду
# На самом деле 3 запроса в 1.2 секунд (для безопасности)
class RatedDriver(LimitRateDriverMixin, HttpDriver):
    requests_per_period = 1
    period = 0.4


class Captcha():
    session = aiohttp.ClientSession()

    async def enter_captcha(self, url, sid):
        if not solver:
            return hues.error('Введите данные для сервиса решения капч в settings.py!')
        with self.session as ses:
            async with ses.get(url) as resp:
                img_data = await resp.read()
                data = solver.solve_captcha(img_data)
                # hues.success(f"Капча {sid} решена успешно")
                return data


class TokenSession(aiovk.TokenSession, Captcha):
    pass


class ImplicitSession(aiovk.ImplicitSession, Captcha):
    pass


class VkPlus(object):
    api = None

    def __init__(self, token=None, login=None, password=None, app_id=5668099, scope=140492191):

        self.group_methods = ('groups.getById', 'groups.getMembers', 'execute')

        self.token = token
        self.login = login
        self.password = password
        self.appid = app_id
        self.scope = scope
        self.init_vk()

    def init_vk(self):
        if self.token:
            self.api_session = TokenSession(access_token=self.token, driver=RatedDriver())
        elif self.login and self.password:
            self.login = self.login
            self.password = self.password
            self.api_session = ImplicitSession(self.login, self.password, self.appid,
                                               scope=self.scope, driver=RatedDriver())  # all scopes
        else:
            fatal('Вы попытались инициализировать объект класса VkPlus без данных для авторизации!')
        self.api = aiovk.API(self.api_session)

        # Паблик API используется для методов, которые не нуждаются в регистрации (users.get и т.д)
        # Используется только при access_token вместо аккаунта
        if self.token:
            self.public_api_session = aiovk.TokenSession(driver=RatedDriver())
            self.public_api = aiovk.API(self.public_api_session)

    async def method(self, key: str, data: dict = {}):
        # Если у нас TOKEN, то для всех остальных методов,
        # кроме разрешённых, вызовем публичное API
        if key not in self.group_methods and self.token and 'message' not in key:
            api_method = self.public_api
        else:
            api_method = self.api
        try:
            return await api_method(key, **data)
        except (asyncio.TimeoutError, json.decoder.JSONDecodeError):
            # Пытаемся отправить запрос к API ещё раз
            return await api_method(key, **data)
        except aiovk.exceptions.VkAuthError:
            message = 'TOKEN' if self.token else 'LOGIN и PASSWORD'
            fatal(f"Произошла ошибка при авторизации API, "
                  "проверьте значение полей {message} в settings.py!")
        except aiovk.exceptions.VkAPIError as ex:
            if ex.error_code == 9:
                # Flood error - слишком много одниаковых сообщений
                if 'message' not in data:
                    return
                # Анти-флуд (комбинация из 5 случайных чисел + латинских букв)
                data['message'] += f'\n Анти-флуд (API): {self.anti_flood()}'
                try:
                    # Пытаемся отправить сообщение с обходом антифлуда
                    await self.method('messages.send', data)
                except aiovk.exceptions.VkAPIError:
                    # В реальности такое будет очень редко
                    # или вообще не случится
                    hues.error('Обход анти-флуда API не удался =(')
            else:
                hues.error(f"Произошла ошибка при вызове метода API {key} с значениями {data}:\n{ex}")

    @staticmethod
    def anti_flood():
        """Функция для обхода антифлуда API ВК"""
        return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(5))

    async def mark_as_read(self, message_ids):
        """Пометить сообщение(я) как прочитанное"""
        await self.method('messages.markAsRead', {'message_ids': message_ids})

    async def resolve_name(self, screen_name):
        """Функция для перевода короткого имени в числовой ID"""
        result = await self.method('utils.resolveScreenName',
                                   {'screen_name': screen_name})
        if result:
            return result['object_id']
        else:
            return None


class Message(object):
    """Класс, объект которого передаётся в плагин для упрощённого ответа"""
    __slots__ = ('_data', 'vk', 'conf', 'user', 'cid', 'id',
                 'body', 'timestamp', 'answer_values', 'attaches')

    def __init__(self, vk_api_object: VkPlus, data: MessageEventData):
        self._data = data
        self.vk = vk_api_object
        self.user = False
        if data.conf:
            self.user = False
            self.cid = int(data.peer_id)
        else:
            self.user = True
        self.id = data.user_id
        self.body = data.body
        self.timestamp = data.time
        self.attaches = data.attaches
        # Словарь для отправки к ВК при ответе
        if self.user:
            self.answer_values = {'user_id': self.id}
        else:
            self.answer_values = {'chat_id': self.cid}

    async def answer(self, msg: str, **additional_values):
        """Функция ответа для упрощения создания плагинов. Так же может принимать доп.параметры"""
        if len(msg) > 550:
            msgs = list(chunks(msg.splitlines(), 15))
        else:
            msgs = [msg]
        if additional_values is None:
            additional_values = dict()
        for msg in msgs:
            data = msgs[0] if not len(msgs) > 1 else '\n'.join(msg)
            values = dict(**self.answer_values, message=data, **additional_values)
            await self.vk.method('messages.send', values)
