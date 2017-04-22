# Standart library
import asyncio
import threading
import json
import shutil

import os
from os.path import abspath, isfile

# 3rd party packages
import aiohttp
import hues

# Custom packages
import pickle

from plugin_system import PluginSystem
from utils import fatal, parse_msg_flags, MessageEventData
from vkplus import VkPlus, Message



class Bot(object):
    """Главный класс бота"""
    __slots__ = ["BLACKLIST", "PREFIXES", "LOG_MESSAGES", "LOG_COMMANDS", "NEED_CONVERT", "APP_ID", "SCOPE", "FLOOD_INTERVAL",
                 "TOKEN", "VK_LOGIN", "VK_PASSWORD",
                 "messages_date", "plugin_system", "cmd_system", "scheduled_funcs", "longpoll_server", "longpoll_key",
                 "event_loop", "last_message_id", "vk", "longpoll_values", "last_ts"]

    def __init__(self):
        self.last_message_id = 0
        self.init_settings()
        self.vk_init()
        self.plugin_init()

    def init_settings(self):
        """Функция инициализации файла настроек и его создания"""
        # Если у нас есть только settings.py.sample
        if isfile('settings.py.sample') and not isfile('settings.py'):
            try:
                shutil.copy('settings.py.sample', 'settings.py')
            except Exception:
                fatal('Я не могу копировать файлы в текущей папке, '
                      'проверьте ваши права на неё!')
            fatal('Был создан файл settings.py, '
                  'не забудьте добавить данные для авторизации!')
        # Если у нас уже есть settings.py
        elif isfile('settings.py'):
            import settings
            try:
                self.BLACKLIST = settings.BLACKLIST
                self.PREFIXES = settings.PREFIXES
                self.LOG_MESSAGES = settings.LOG_MESSAGES
                self.LOG_COMMANDS = settings.LOG_COMMANDS
                self.NEED_CONVERT = settings.NEED_CONVERT
                self.APP_ID = settings.APP_ID
                self.SCOPE = settings.SCOPE
                self.FLOOD_INTERVAL = settings.FLOOD_INTERVAL
                # Настройки по умолчанию
                self.TOKEN = None
                self.VK_LOGIN = None
                self.VK_PASSWORD = None
                # Если в настройках есть токен
                if settings.TOKEN:
                    self.TOKEN = settings.TOKEN
                # Есои есть логин и пароль
                if settings.LOGIN and settings.PASSWORD:
                    self.VK_LOGIN = settings.LOGIN
                    self.VK_PASSWORD = settings.PASSWORD

                if not self.TOKEN and not(self.VK_LOGIN and self.VK_PASSWORD):
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
        self.vk = VkPlus(token=self.TOKEN,
                         login=self.VK_LOGIN,
                         password=self.VK_PASSWORD,
                         scope=self.SCOPE,
                         app_id=self.APP_ID)

        hues.success("Успешная авторизация")

    def plugin_init(self):
        hues.warn("Загрузка плагинов...")

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
                                        self.plugin_system, self.NEED_CONVERT)
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
        # Если ID находится в чёрном списке
        if peer_id in self.BLACKLIST:
            return
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

        cleaned_body = text.replace('<br>', '\n')

        data = MessageEventData(conf, peer_id, user_id, cleaned_body, ts, msg_id, attaches)

        try:
            # Проверяем на интервал между командами для этого ID пользователя
            if ts - self.messages_date[user_id] <= self.FLOOD_INTERVAL:
                self.messages_date[user_id] = ts
                return
            else:
                self.messages_date[user_id] = ts
        except KeyError:
            self.messages_date[user_id] = ts
        await self.check_if_command(data, msg_id)

    async def check_if_command(self, data: MessageEventData, msg_id: int) -> None:
        msg_obj = Message(self.vk, data)
        result = await self.cmd_system.process_command(msg_obj)
        if self.LOG_MESSAGES:
            who = f"{'конференции' if data.conf else 'ЛС'} {data.peer_id}"
            hues.info(f"Сообщение из {who} > {data.body}")

    def schedule_coroutine(self, target):
        """Schedules target coroutine in the given event loop
        If not given, *loop* defaults to the current thread's event loop
        Returns the scheduled task.
        """
        if asyncio.iscoroutine(target):
            return asyncio.ensure_future(target, loop=self.event_loop)
        else:
            raise TypeError("target must be a coroutine, "
                          "not {!r}".format(type(target)))

    async def run(self, event_loop):
        """Главная функция бота - тут происходит ожидание новых событий (сообщений)"""
        self.event_loop = event_loop  # Нужен для шедулинга функций

        await self.init_long_polling()
        session = aiohttp.ClientSession(loop=event_loop)
        while True:
            try:
                resp = await session.get(self.longpoll_server,
                                         params=self.longpoll_values)
            except aiohttp.errors.ClientOSError:
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
                self.schedule_coroutine(self.check_event(event))

if __name__ == '__main__':
    bot = Bot()
    hues.success("Приступаю к приему сообщений")
    main_loop = asyncio.get_event_loop()
    # запускаем бота
    try:
        main_loop.run_until_complete(bot.run(main_loop))
    except KeyboardInterrupt:
        hues.warn("Сохраняю данные плагинов...")

        if not os.path.exists("plugins/temp"):
            os.makedirs("plugins/temp")

        for plugin in bot.plugin_system.get_plugins():
            if plugin.data and any(plugin.data.values()):
                with open(f'plugins/temp/{plugin.name.lower().replace(" ", "_")}.data', 'wb') as f:
                    pickle.dump(plugin.data, f)

        hues.warn("Выключение бота...")
        exit()
    except Exception as ex:
        import traceback

        hues.error("Произошла фатальная ошибка во время работы:\n")
        traceback.print_exc()
        # Закрываем сессии API (чтобы не было предупреждения)
        bot.vk.api_session.close()
        if bot.TOKEN:
            bot.vk.public_api_session.close()
        exit(1)
