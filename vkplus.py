# Standart library
import asyncio
import json
import random
import string

import aiohttp
import aiovk
import hues

from aiovk.drivers import HttpDriver, Socks5Driver
from aiovk.mixins import LimitRateDriverMixin
from captcha_solver import CaptchaSolver

from methods import is_available_from_group
from methods import is_available_from_public
from utils import fatal, MessageEventData, chunks, Attachment, unquote, quote, RequestFuture, schedule_coroutine, \
    SendFrom

solver = None

try:
    from settings import CAPTCHA_KEY, CAPTCHA_SERVER, TOKEN, SCOPE, APP_ID

    if CAPTCHA_KEY and CAPTCHA_KEY:
        solver = CaptchaSolver(CAPTCHA_SERVER, api_key=CAPTCHA_KEY)
except (ImportError, AttributeError):
    pass


class NoPermissions(Exception):
    pass


async def enter_captcha(url, sid):
    if not solver:
        return hues.warn('Введите данные для сервиса решения капч в settings.py!')

    session = aiohttp.ClientSession()

    with session as ses:
        async with ses.get(url) as resp:
            img_data = await resp.read()
            data = solver.solve_captcha(img_data)
            return data


async def enter_confirmation_сode():
    hues.error("Похоже, у вас утсановлена двухфакторная авторизация!")
    hues.error("Пожалуйста, введите код подтверждения:")

    code = input()

    hues.success("Спасибо! Продолжаю приём сообщений")

    return code


class TokenSession(aiovk.TokenSession):
    async def enter_captcha(self, url, sid):
        await enter_captcha(url, sid)


class ImplicitSession(aiovk.ImplicitSession):
    async def enter_captcha(self, url, sid):
        await enter_captcha(url, sid)

    async def enter_confirmation_сode(self):
        await enter_confirmation_сode()


class RatedDriver(LimitRateDriverMixin, HttpDriver):
    requests_per_period = 3
    period = 1


class RatedDriverProxy(LimitRateDriverMixin, Socks5Driver):
    requests_per_period = 3
    period = 1


class VkPlus(object):
    def __init__(self, bot, users_data: list=[], proxies: list=[], app_id: int=5982451, scope=140489887):
        self.bot = bot
        self.users = []
        self.tokens = []
        self.scope = scope
        self.group = False
        self.app_id = app_id
        self.proxies = proxies
        self.users_data = users_data
        self.current_user = 0
        self.current_token = 0

        self.init_vk()

        self.queues = [asyncio.Queue(), asyncio.Queue()]

        schedule_coroutine(self.handle_queues())

    async def handle_queues(self):
        while True:
            for i in range(len(self.queues)):
                if await self.process_queue(self.queues[i], i):
                    await asyncio.sleep(0.33)

            await asyncio.sleep(0.1)

    async def process_queue(self, queue, queue_id):
        if not queue.empty():
            execute = "return ["

            tasks = []

            for i in range(25):
                task = queue.get_nowait()

                if task.data is None:
                    task.data = {}

                execute += 'API.' + task.key + '({'
                execute += ", ".join((f"{k}: \"" + str(v).replace('"', '\\"') + "\"") for k, v in task.data.items())
                execute += '}), '

                tasks.append(task)

                if queue.empty():
                    break

            execute += "];"

            result = await self.execute(execute, SendFrom(queue_id))

            for task in tasks:
                if result:
                    task_result = result.pop(0)

                    if task_result is False:
                        hues.error(f"Ошибка! Метод \"{task.key}\" нельзя вызвать с вашими данными!")
                        hues.error(f"Или введите данные пользователя, или данные группы, чтобы всё работало!")
                        hues.error(f"Или проблема с доступом к вконтакте!")

                    task.set_result(task_result)

                else:
                    task.set_result(None)

            return True
        return False

    def init_vk(self):
        """Инициализация сессий ВК API"""
        current_proxy = 0

        for user in self.users_data:
            if self.proxies:
                proxy = self.proxies[current_proxy % len(self.proxies)]
                current_proxy += 1

            driver = RatedDriver() if not self.proxies else RatedDriverProxy(*proxy)

            if len(user) == 1:
                session = TokenSession(
                    user[0],
                    driver=driver
                )

                api = aiovk.API(session)

                if api:
                    self.group = True
                    self.tokens.append(aiovk.API(session))

            else:
                session = ImplicitSession(
                    user[0],
                    user[1],
                    self.app_id,
                    scope=140489887,
                    driver=driver
                )

                api = aiovk.API(session)

                if api:
                    self.users.append(aiovk.API(session))

    async def execute(self, code, send_from=SendFrom.GROUP):
        api_method = None

        if self.users and send_from == SendFrom.USER:
            api_method = self.users[self.current_user % len(self.users)]
            self.current_user += 1

        elif self.tokens and send_from == SendFrom.GROUP:
            api_method = self.tokens[self.current_token % len(self.tokens)]
            self.current_token += 1

        if not api_method:
            hues.error("Ошибка при выполнении execute:")
            hues.error(code)
            hues.error("Возможно, эти запросы невозможно выполнить из-за ограничений доступа.")
            hues.error(f"Доступ: {send_from}")
            return

        try:
            return unquote(await api_method("execute", code=quote(code)))

        except (asyncio.TimeoutError, json.decoder.JSONDecodeError):
            # Пытаемся отправить запрос к API ещё раз
            return unquote(await api_method("execute", code=quote(code)))

        except aiovk.exceptions.VkAuthError:
            message = 'TOKEN' if self.token else 'LOGIN и PASSWORD'
            fatal("Произошла ошибка при авторизации API, "
                  f"проверьте значение {message} в settings.py!")

    async def method(self, key: str, data=None, send_from=None):
        """Выполняет метод API VK с дополнительными параметрами"""
        if key != "execute":
            if send_from is None:
                if self.group and is_available_from_group(key):
                    send_from = SendFrom.GROUP

                elif is_available_from_public(key):
                    if not self.users:
                        hues.error("Вы пытаетесь вызвать публичный метод, для которого нужен акаунт пользователя!\n"
                                   "Но у вас не установлен ни один пользователь!")

                    send_from = SendFrom.USER

                else:
                    send_from = SendFrom.USER

            task = RequestFuture(key, data, send_from)

            self.queues[send_from.value].put_nowait(task)

            return await asyncio.wait_for(task, None)

    async def upload_photo(self, encoded_image) -> Attachment:
        data = aiohttp.FormData()
        data.add_field('photo',
                       encoded_image,
                       filename='picture.png',
                       content_type='multipart/form-data')

        upload_url = (await self.method('photos.getMessagesUploadServer'))['upload_url']

        async with aiohttp.ClientSession() as sess:
            async with sess.post(upload_url, data=data) as resp:
                result = json.loads(await resp.text())

        if not result:
            return None

        data = dict(photo=result['photo'], hash=result['hash'], server=result['server'])
        result = (await self.method('photos.saveMessagesPhoto', data))[0]

        link = ""
        for k in result:
            if "photo_" in k:
                link = result[k]

        return Attachment("photo", result["owner_id"], result["id"], "", link)

    @staticmethod
    def anti_flood():
        """Возвращает строку из 5 символов (букв и цифр)"""
        return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(5))

    async def mark_as_read(self, message_ids):
        """Отмечает сообщение(я) как прочитанное(ые)"""
        await self.method('messages.markAsRead', {'message_ids': message_ids})

    async def resolve_name(self, screen_name):
        """Функция для перевода короткого имени в числовой ID"""
        try:
            for val in ('club', 'public', 'event'):
                screen_name = screen_name.replace(val, '')
            possible_id = int(screen_name)
            return possible_id

        except ValueError:
            result = await self.method('utils.resolveScreenName',
                                       {'screen_name': screen_name})
            if not result:
                return False

            return result.get('object_id')


class Message(object):
    """Класс, объект которого передаётся в плагин для упрощённого ответа"""
    __slots__ = ('_data', 'vk', 'conf', 'user', 'cid', 'id',
                 'body', 'timestamp', 'answer_values', 'brief_attaches', '_full_attaches', 'msg_id')

    def __init__(self, vk_api_object: VkPlus, data: MessageEventData):
        self._data = data
        self.vk = vk_api_object
        self.user = False
        # Если сообщение из конференции
        if data.conf:
            self.user = False
            self.cid = int(data.peer_id)
        else:
            self.user = True
        self.id = data.user_id
        self.body = data.body
        self.msg_id = data.msg_id
        self.timestamp = data.time
        self.brief_attaches = data.attaches
        self._full_attaches = []
        # Словарь для отправки к ВК при ответе
        if self.user:
            self.answer_values = {'user_id': self.id}
        else:
            self.answer_values = {'chat_id': self.cid}

    @property
    async def full_attaches(self):
        # Если мы уже получали аттачи для этого сообщения, возвратим их
        if self._full_attaches:
            return self._full_attaches

        values = {'message_ids': self.msg_id,
                  'preview_length': 1}
        # Получаем полную информацию о сообщении в ВК (включая аттачи)
        full_message_data = await self.vk.method('messages.getById', values)

        if not full_message_data:
            # Если пришёл пустой ответ от VK API
            return []

        message = full_message_data['items'][0]
        if "attachments" not in message:
            # Если нет аттачей
            return
        # Проходимся по всем аттачам
        for raw_attach in message["attachments"]:
            # Тип аттача
            a_type = raw_attach['type']
            # Получаем сам аттач
            attach = raw_attach[a_type]

            link = ""
            # Ищём ссылку на фото
            for k, v in attach.items():
                if "photo_" in k:
                    link = v
            # Получаем access_key для аттача
            key = attach.get('access_key')
            attach = Attachment(a_type, attach['owner_id'], attach['id'], key, link)
            # Добавляем к нашему внутреннему списку аттачей
            self._full_attaches.append(attach)

        return self._full_attaches

    async def answer(self, msg: str, **additional_values):
        """Функция ответа на сообщение для плагинов"""
        # Если длина сообщения больше 550 символов (получено эмпирическим путём)
        if len(msg) > 550:
            # Делим сообщение на список частей (каждая по 15 строк)
            msgs = list(chunks(msg, 15))
        else:
            # Иначе - создаём список из нашего сообщения
            msgs = [msg]
        if additional_values is None:
            additional_values = dict()
        # Отправляем каждое сообщение из списка
        for msg in msgs:
            data = msgs[0] if not len(msgs) > 1 else '\n'.join(msgs)
            values = dict(**self.answer_values, message=data, **additional_values)
            await self.vk.method('messages.send', values)
