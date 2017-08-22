# Standart library
import asyncio
import json
import logging
import shutil
from os.path import abspath, isfile

import aiohttp
import hues

from chat.chatter import normalize, ChatterBot
from command import Command
from database import *
from plugin_system import PluginSystem
from utils import fatal, parse_msg_flags, MessageEventData, schedule_coroutine
from vkplus import VkPlus, Message


class Bot(object):
    """Главный класс бота"""
    __slots__ = ["PREFIXES", "LOG_MESSAGES", "LOG_COMMANDS", "WHITELISTED",
                 "FLOOD_INTERVAL", "USERS", "PROXIES", "SCOPE", "APP_ID",
                 "DATABASE_CHARSET", "ONLY_CHAT", "USE_CHATTER", "DO_CHAT",
                 "IGNORE_PREFIX", "BLACKLIST_MESSAGE", "WHITELIST_MESSAGE",
                 "messages_date", "plugin_system", "cmd_system", "last_ts",
                 "scheduled_funcs", "longpoll_server", "longpoll_key", "chatter",
                 "longpoll_values", "event_loop", "last_message_id", "vk"]

    def __init__(self):
        self.init_settings()
        self.vk_init()
        self.plugin_init()

        if self.DO_CHAT:
            if self.USE_CHATTER:
                self.chatter = ChatterBot()
            else:
                from chat.chat import chatter
                self.chatter = chatter

    def init_settings(self):
        """Функция инициализации файла настроек и его создания"""
        # Если у нас есть только settings.py.sample
        if isfile('settings.py.sample') and not isfile('settings.py'):
            try:
                shutil.copy('settings.py.sample', 'settings.py')
            except Exception:
                fatal('Я не могу копировать файлы в текущей папке, '
                      'проверьте ваши права на неё!')
            hues.info('Был создан файл settings.py, '
                      'не забудьте добавить данные для авторизации!')
            exit()
        # Если у нас уже есть settings.py
        elif isfile('settings.py'):
            import settings
            try:
                self.WHITELISTED = False
                self.WHITELIST_MESSAGE = settings.WHITELIST_MESSAGE
                self.BLACKLIST_MESSAGE = settings.BLACKLIST_MESSAGE

                self.PREFIXES = settings.PREFIXES

                self.LOG_MESSAGES = settings.LOG_MESSAGES
                self.LOG_COMMANDS = settings.LOG_COMMANDS

                self.APP_ID = settings.APP_ID
                self.SCOPE = settings.SCOPE

                self.FLOOD_INTERVAL = settings.FLOOD_INTERVAL

                self.USERS = settings.USERS
                self.PROXIES = settings.PROXIES

                self.DO_CHAT = settings.DO_CHAT
                self.ONLY_CHAT = settings.ONLY_CHAT
                self.USE_CHATTER = settings.USE_CHATTER
                self.IGNORE_PREFIX = settings.IGNORE_PREFIX

                settings.ADMINS
                settings.BLACKLIST
                settings.WHITELIST

                if not self.USERS:
                    fatal("Проверьте, что у есть LOGIN и PASSWORD, или же TOKEN в файле settings.py!"
                          "Без них бот работать НЕ СМОЖЕТ.")

            except (ValueError, AttributeError, NameError):
                fatal('Проверьте содержимое файла settings.py, возможно вы удалили что-то нужное!')
        # Если не нашли ни settings.py, ни settings.py.sample
        else:
            fatal("settings.py и settings.py.sample не найдены, возможно вы их удалили?")

    def vk_init(self):
        hues.warn("Авторизация в ВКонтакте...")
        # Словарь вида ID -> время
        self.messages_date = {}
        self.vk = VkPlus(users_data=self.USERS,
                         proxies=self.PROXIES,
                         bot=self,
                         scope=self.SCOPE,
                         app_id=self.APP_ID)
        if self.vk:
            hues.success("Успешная авторизация")

    def plugin_init(self):
        hues.info("Загрузка плагинов...")

        # Подгружаем плагины
        self.plugin_system = PluginSystem(self.vk, folder=abspath('plugins'))
        self.plugin_system.register_commands()
        # Чтобы плагины могли получить список всех плагинов (костыль)
        self.vk.get_plugins = self.plugin_system.get_plugins

        # Для парсинга команд с пробелом используется
        # обратная сортировка, для того, чтобы самые
        # длинные команды были первыми в списке
        command_names = list(self.plugin_system.commands.keys())
        command_names.sort(key=len, reverse=True)

        from command import CommandSystem
        self.cmd_system = CommandSystem(command_names,
                                        self.plugin_system)
        self.scheduled_funcs = self.plugin_system.scheduled_events
        hues.success("Загрузка плагинов завершена")

    async def init_long_polling(self, update=0):
        """Функция для инициализации Long Polling"""
        retries = 5
        for x in range(retries):
            result = await self.vk.method('messages.getLongPollServer', {'use_ssl': 1})
            if result:
                break

        if not result:
            fatal("Не удалось получить значения Long Poll сервера!")

        try:
            self.last_ts = self.longpoll_values['ts']
            self.longpoll_key = self.longpoll_values['key']
        except AttributeError:
            pass
        except ValueError:
            pass

        if update == 0:
            # Если нам нужно инициализировать с нуля, меняем сервер
            self.longpoll_server = "https://" + result['server']
        if update in (0, 3):
            # Если нам нужно инициализировать с нуля, или ошибка 3
            self.longpoll_key = result['key']
            self.last_ts = result['ts']  # Последний timestamp
        elif update == 2:
            # Если ошибка 2 - то нужен новый ключ
            self.longpoll_key = result['key']

        self.longpoll_values = {
            'act': 'a_check',
            'key': self.longpoll_key,
            'ts': self.last_ts,
            'wait': 25,  # Тайм-аут запроса
            'mode': 10,
            'version': 1
        }

    async def check_event(self, new_event):
        if not new_event:
            return  # На всякий случай

        event_id = new_event.pop(0)

        if event_id != 4:
            return  # Если событие - не новое сообщение

        msg_id, flags, peer_id, ts, subject, text, attaches = new_event

        # Получаем параметры сообщения
        # https://vk.com/dev/using_longpoll_2
        flags = parse_msg_flags(flags)
        # Если сообщение - исходящее
        if flags['outbox']:
            return

        # Тип сообщения - конференция или ЛС?
        try:
            # Пробуем получить ID пользователя, который отправил
            # сообщение в беседе
            user_id = attaches['from']
            peer_id -= 2000000000
            conf = True
        except KeyError:
            # Если ключа from нет - это ЛС
            user_id = peer_id
            conf = False
        user_id = int(user_id)
        
         # Если ID находится в чёрном списке
        if await get_or_none(Role, user_id=user_id, role="blacklisted"):
            if self.BLACKLIST_MESSAGE:
                await self.vk.method("messages.send", {"user_id": user_id, "message": self.BLACKLIST_MESSAGE})

            return

        if self.WHITELISTED and not await get_or_none(Role, user_id=user_id, role="whitelisted"):
            if self.WHITELIST_MESSAGE:
                await self.vk.method("messages.send", {"user_id": user_id, "message": self.WHITELIST_MESSAGE})

            return

        cleaned_body = text.replace('<br>', '\n')

        data = MessageEventData(conf, peer_id, user_id, cleaned_body, ts, msg_id, attaches)

        user = await get_or_none(User, uid=user_id)
        if user:
            if ts - user.message_date <= self.FLOOD_INTERVAL:
                user.message_date = ts
                await db.update(user)
                return

            user.message_date = ts

            await db.update(user)
        else:
            user = await db.create(User, uid=user_id)

        await self.check_if_command(data, user)

    async def do_chat(self, msg, user):
        if not self.DO_CHAT:
            return

        if user.chat_data:
            chat_data = json.loads(user.chat_data)
            chat_data.append(normalize(msg.text))
            chat_data = chat_data[::-1]
        else:
            chat_data = [normalize(msg.text)]

        answer = self.chatter.parse_message(chat_data)

        if answer is not None:
            chat_data = chat_data[::-1]
            chat_data.append(normalize(answer))

            user.chat_data = json.dumps(chat_data)

            await db.update(user)

            await msg.answer(answer)

    async def check_if_command(self, data: MessageEventData, user) -> None:
        if self.LOG_MESSAGES:
            who = f"{'конференции' if data.conf else 'ЛС'} {data.peer_id}"
            hues.info(f"Сообщение из {who} > {data.body}")

        msg_obj = Message(self.vk, data, user)

        cmd = Command(msg_obj)

        if not cmd.has_prefix:
            if self.DO_CHAT and self.IGNORE_PREFIX:
                await self.do_chat(msg_obj, user)

            return

        if self.ONLY_CHAT and self.DO_CHAT:
            await self.do_chat(msg_obj, user)

        else:
            result = await self.cmd_system.process_command(msg_obj, cmd)

            if result is False:
                await self.do_chat(msg_obj, user)

    async def run(self, event_loop):
        """Главная функция бота - тут происходит ожидание новых событий (сообщений)"""
        self.event_loop = event_loop  # Нужен для шедулинга функций

        await self.init_long_polling()
        session = aiohttp.ClientSession(loop=event_loop)
        while True:
            try:
                resp = await session.get(self.longpoll_server,
                                         params=self.longpoll_values)
            except (aiohttp.ClientOSError, asyncio.TimeoutError):
                # У меня были такие ошибки на Manjaro 16.10.3 Fringilla
                # ВК почему-то присылал сервер, к которому нельзя подключиться
                hues.warn('Сервер Long Polling не отвечает, подключаюсь к другому...')
                await self.init_long_polling()
                continue
            """
            Тут не используется resp.json() по простой причине:
            aiohttp будет писать warning'и из-за плохого mimetype
            Неизвестно, почему он у ВК такой - text/javascript; charset=utf-8
            """
            events_text = await resp.text()
            try:
                events = json.loads(events_text)
            except ValueError:
                # В JSON ошибка, или это вовсе не JSON
                continue

            # Проверяем на код ошибки
            failed = events.get('failed')
            if failed:
                err_num = int(failed)
                # Код 1 - Нам нужно обновить timestamp
                if err_num == 1:
                    self.longpoll_values['ts'] = events['ts']
                # Коды 2 и 3 - нужно запросить данные нового
                # Long Polling сервера
                elif err_num in (2, 3):
                    await self.init_long_polling(err_num)
                continue

            # Обновляем время, чтобы не приходили старые события
            self.longpoll_values['ts'] = events['ts']
            for event in events['updates']:
                schedule_coroutine(self.check_event(event))


if __name__ == '__main__':
    hues.info("Приступаю к запуску VBot v5.0")

    bot = Bot()

    main_loop = asyncio.get_event_loop()
    main_loop.run_until_complete(set_up_roles(bot))

    hues.success("Приступаю к приему сообщений")

    try:
        main_loop.run_until_complete(bot.run(main_loop))
    except (KeyboardInterrupt, SystemExit):
        hues.warn("Выключение бота...")

    except Exception as ex:
        import traceback

        logging.warning("Fatal error:\n")
        traceback.print_exc()

        exit(1)
