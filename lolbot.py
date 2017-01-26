# Standart library
import json
from os.path import abspath, isfile
import shutil
import asyncio

# 3rd party packages
import aiohttp
import hues

# Custom packages
from plugin_system import PluginSystem
from vkplus import VkPlus, Message
from utils import fatal, parse_msg_flags, schedule


class Bot(object):
    """Главный класс бота, создан для упрощённой работы с переменными"""

    def __init__(self):
        # По умолчанию все сообщения будут жирные и синие :)

        self.last_message_id = 0
        self.init_settings()
        self.vk_init()
        self.plugin_init()
        asyncio.sleep(0.35)  # успеть всё инициализировать

    def init_settings(self):
        """Функция инициализации файла настроек и его создания"""
        # Если у нас есть только settings.py.sample
        if isfile('settings.py.sample') and not isfile('settings.py'):
            try:
                shutil.copy('settings.py.sample', 'settings.py')
            except Exception:
                fatal('У меня нет прав писать в текущую директорию, '
                      'проверьте ваши права на неё!')
            fatal('Был создан файл settings.py, пожалуйста, измените значения на Ваши!')
        # Если у нас уже есть settings.py
        elif isfile('settings.py'):
            import settings
            try:
                self.BLACKLIST = settings.BLACKLIST
                self.PREFIXES = settings.PREFIXES
                self.log_messages = settings.NEED_LOG
                self.convert_layout = settings.NEED_CONVERT
                self.app_id = settings.APP_ID
                self.scope = settings.SCOPE
                if settings.TOKEN:
                    self.is_token = True
                    self.token = settings.TOKEN

                elif settings.LOGIN and settings.PASSWORD:
                    self.is_token = False
                    self.vk_login = settings.LOGIN
                    self.vk_password = settings.PASSWORD
                else:
                    fatal('Проверьте, что у вас заполнены LOGIN и PASSWORD, или же TOKEN!'
                          'Без них бот работать НЕ СМОЖЕТ.')

            except (ValueError, IndexError, AttributeError, NameError):
                fatal('Проверьте содержимое файла settings.py, возможно вы удалили что-то нужное!')
        # Если не нашли ни settings.py, ни settings.py.sample
        else:
            fatal('settings.py и settings.py.sample не найдены, возможно вы их удалили?')

    def vk_init(self):
        hues.warn('Авторизация в вк...')
        # Словарь вида ID -> время
        self.messages_date = {}
        if self.is_token:
            self.vk = VkPlus(token=self.token, scope=self.scope, app_id=self.app_id)
        elif not self.is_token:
            self.vk = VkPlus(login=self.vk_login, password=self.vk_password, scope=self.scope, app_id=self.app_id)

        self.ANSWER_VALUES = {
            'out': 0,
            'offset': 0,
            'count': 20,
            'time_offset': 15,
            'filters': 0,
            'preview_length': 0,
            'last_message_id': self.last_message_id
        }

        hues.success('Успешная авторизация')

    def plugin_init(self):
        hues.warn("Загрузка плагинов...")

        # Подгружаем плагины
        self.plugin_system = PluginSystem(folder=abspath('plugins'))
        self.plugin_system.register_commands()
        # Чтобы плагины могли получить список плагинов (костыль)
        self.vk.get_plugins = self.plugin_system.get_plugins

        # Для парсинга команд с пробелом используется
        # обратная сортировка, для того, чтобы самые
        # длинные команды были первыми в списке
        command_names = list(self.plugin_system.commands.keys())
        command_names.sort(key=len, reverse=True)

        from command import CommandSystem
        self.cmd_system = CommandSystem(command_names, self.plugin_system, self.convert_layout)
        self.scheduled_funcs = self.plugin_system.scheduled_events
        hues.success("Загрузка плагинов завершена")

    async def init_long_polling(self):
        """Функция для инициализации Long Polling"""
        result = await self.vk.method('messages.getLongPollServer',
                                      {'use_ssl': 1})
        if not result:
            fatal('Не удалось получить значения Long Poll сервера!')
        self.longpoll_server = "https://" + result['server']
        self.longpoll_key = result['key']
        self.last_ts = result['ts']  # Последний timestamp
        self.longpoll_values = {
            'act': 'a_check',
            'key': self.longpoll_key,
            'ts': self.last_ts,
            'wait': 20,  # Тайм-аут запроса
            'mode': 2,
            'version': 1
        }

    async def check_event(self, new_event):
        if not new_event:
            return  # На всякий случай
        if not new_event[0] == 4:
            return  # Если событие - не новое сообщение

        msg_id, flags, peer_id, ts, subject, text, attaches = new_event[1:]
        # Если ID находится в чёрном списке
        if peer_id in self.BLACKLIST:
            return
        # Получаем параметры сообщения
        # https://vk.com/dev/using_longpoll_2
        flags = parse_msg_flags(flags)
        if flags['outbox']:
            # Если сообщение - исходящее
            return

        # Тип сообщения - конференция или ЛС?
        try:
            # Пробуем получить ID пользователя, который отправил
            # сообщение в беседе
            user_id = attaches['from']
            peer_id -= 2000000000
            msg_type = 'chat_id'
        except KeyError:
            # Если ключа from нет - это ЛС
            user_id = peer_id
            msg_type = 'user_id'
        data = {
            msg_type: peer_id,
            'uid': user_id,  # uid - ID пользователя (в беседе или в ЛС)
            'body': text.replace('<br>', '\n'),
            'date': ts
        }
        try:
            # Если разница между сообщениями меньше 1 сек - игнорим
            if ts - self.messages_date[user_id] <= 1:
                self.messages_date[user_id] = ts
                return
            else:
                self.messages_date[user_id] = ts
        except KeyError:
            self.messages_date[user_id] = ts
        await self.check_if_command(data, msg_id)

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
        #for func in self.scheduled_funcs:
        #    self.schedule_coroutine(func)
        await self.init_long_polling()
        session = aiohttp.ClientSession()
        while True:
            resp = await session.get(self.longpoll_server,
                                     params=self.longpoll_values)
            """
            Тут не используется resp.json() по простой причине:
            aiohttp будет писать warning'и из-за плохого mimetype
            Неизвестно, почему он у ВК такой - text/javascript; charset=utf-8
            """
            events_text = await resp.text()
            try:
                events = json.loads(events_text)
            except ValueError:
                continue  # Отправляем запрос ещё раз
            # Проверяем на код ошибки
            failed = events.get('failed')
            if failed:
                err_num = int(failed)
                # Код 1 - Нам нужно обновить time stamp
                if err_num == 1:
                    self.longpoll_values['ts'] = events['ts']
                # Коды 2 и 3 - нужно переподключиться к long polling серверу
                elif err_num == 2:
                    await self.init_long_polling()
                elif err_num == 3:
                    await self.init_long_polling()
                continue
            # Обновляем время, чтобы не приходили старые события
            self.longpoll_values['ts'] = events['ts']
            for event in events['updates']:
                await self.check_event(event)

    async def check_if_command(self, answer: dict, msg_id: int) -> None:
        # Если не нужно логгировать сообщения
        if not self.log_messages:
            msg_obj = Message(self.vk, answer)
            result = await self.cmd_system.process_command(msg_obj)
            if result:
                # Если мы распознали команду, то помечаем её прочитанной
                return await self.vk.mark_as_read(msg_id)
        if 'chat_id' in answer:
            hues.info("Сообщение из конференции ({}) > {}".format(
                answer['chat_id'], answer['body']
            ))
        elif 'user_id' in answer:
            hues.info("Сообщение из ЛС http://vk.com/id{} > {}".format(
                answer['user_id'], answer['body']
            ))


if __name__ == '__main__':
    bot = Bot()
    hues.success('Приступаю к приему сообщений')
    loop = asyncio.get_event_loop()
    # запускаем бота
    try:
        loop.run_until_complete(bot.run(loop))
    except KeyboardInterrupt:
        hues.warn("Выключение бота...")
        exit()
    except Exception as ex:
        import traceback

        hues.error("Фатальная ошибка при выполнении бота:\n")
        traceback.print_exc()
        # Закрываем сессии API (чтобы не было предупреждения)
        bot.vk.api_session.close()
        if bot.is_token:
            bot.vk.public_api_session.close()
        exit(1)
