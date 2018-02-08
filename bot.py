import aiohttp
import signal
import json

import logging
import asyncio
from asyncio import Future, Task

import time
from aiohttp import web
from os import getenv

from handler.handler_controller import MessageHandler
from utils import parse_msg_flags
from vk.plus import VkController

from vk.data import Message, LongpollEvent, ChatChangeEvent, CallbackEvent
from vk.utils import MessageEventData


class Bot:
    __slots__ = ("logger", "loop", "values", "server", "main_task", "longpoll_request",
                 "settings", "api", "handler", "logger_file")

    def __init__(self, settings, logger=None, handler=None, loop=asyncio.get_event_loop()):
        self.settings = settings

        self.logger = None
        self.init_logger(logger)

        self.logger.info("Initializing bot")

        self.loop = loop

        self.values = {}
        self.server = ""
        self.longpoll_request = None

        self.main_task = None

        self.logger.info("Initializing vk clients")
        self.api = VkController(settings, logger=self.logger)

        self.logger.info("Loading plugins")
        if handler:
            self.handler = handler

        else:
            self.handler = MessageHandler(self, self.api, initiate_plugins=False)
            self.handler.initiate_plugins()

        signal.signal(signal.SIGINT, lambda x, y: self.stop_bot(True))

        self.logger.info("Bot successfully initialized")

    def init_logger(self, logger):
        if not logger:
            logger = logging.Logger("sketal", level=logging.DEBUG if self.settings.DEBUG else logging.INFO)

        formatter = logging.Formatter(fmt=u'%(filename)-10s [%(asctime)s] %(levelname)-8s: %(message)s',
                                      datefmt='%y.%m.%d %H:%M:%S')

        file_handler = logging.FileHandler('logs.txt')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)

        self.logger_file = file_handler

        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(level=logging.DEBUG if self.settings.DEBUG else logging.INFO)
        stream_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)

        self.logger = logger

    async def init_long_polling(self, update=0):
        result = None
        retries = 10
        for _ in range(retries):
            result = await self.api(sender=self.api.target_client).messages.getLongPollServer(use_ssl=1, lp_version=2)

            if result:
                break

            time.sleep(0.5)

        if not result:
            self.logger.error("Unable to connect to VK's long polling server")
            exit()

        last_ts = 0
        longpoll_key = ""

        if 'ts' in self.values:
            last_ts = self.values['ts']

        if 'key' in self.values:
            longpoll_key = self.values['key']

        if update == 0:
            self.server = "https://" + result['server']
            longpoll_key = result['key']
            last_ts = result['ts']

        elif update == 3:
            longpoll_key = result['key']
            last_ts = result['ts']

        elif update == 2:
            longpoll_key = result['key']

        self.values = {
            'act': 'a_check',
            'key': longpoll_key,
            'ts': last_ts,
            'wait': 20,
            'mode': 10,
            'version': 2
        }

    async def process_longpoll_event(self, new_event):
        if not new_event:
            return

        event_id = new_event[0]

        if event_id != 4:
            evnt = LongpollEvent(self.api, event_id, new_event)

            return await self.process_event(evnt)

        data = MessageEventData()
        data.msg_id = new_event[1]
        data.attaches = new_event[6]
        data.time = int(new_event[4])

        try:
            data.user_id = int(data.attaches['from'])
            data.chat_id = int(new_event[3]) - 2000000000
            data.is_multichat = True

            del data.attaches['from']

        except KeyError:
            data.user_id = int(new_event[3])
            data.is_multichat = False

        # https://vk.com/dev/using_longpoll_2
        flags = parse_msg_flags(new_event[2])

        if flags['outbox']:
            if not self.settings.READ_OUT:
                return

            data.is_out = True

        data.full_text = new_event[5].replace('<br>', '\n')

        if "fwd" in data.attaches:
            data.forwarded = MessageEventData.parse_brief_forwarded_messages_from_lp(data.attaches["fwd"])
            del data.attaches["fwd"]

        else:
            data.forwarded = []

        msg = Message(self.api, data)

        if await self.check_event(data.user_id, data.chat_id, data.attaches):
            msg.is_event = True

        await self.process_message(msg)

    async def longpoll_processor(self):
        await self.init_long_polling()

        session = aiohttp.ClientSession(loop=self.loop)

        while True:
            try:
                self.longpoll_request = session.get(self.server, params=self.values)

                resp = await self.longpoll_request

            except aiohttp.ClientOSError:
                session = aiohttp.ClientSession(loop=self.loop)

            except (asyncio.TimeoutError, aiohttp.ServerDisconnectedError):
                self.logger.warning("Long polling server doesn't respond. Changing server")
                await self.init_long_polling()
                continue

            try:
                events = json.loads(await resp.text())
            except ValueError:
                continue

            failed = events.get('failed')

            if failed:
                err_num = int(failed)

                if err_num == 1:  # 1 - update timestamp
                    self.values['ts'] = events['ts']

                elif err_num in (2, 3):  # 2, 3 - new data for long polling
                    await self.init_long_polling(err_num)

                continue

            self.values['ts'] = events['ts']
            for event in events['updates']:
                asyncio.ensure_future(self.process_longpoll_event(event))

    async def callback_processor(self, request):
        try:
            data = await request.json()

        except (UnicodeDecodeError, json.decoder.JSONDecodeError):
            return web.Response(text="ok")

        data_type = data["type"]

        if data_type == "confirmation":
            return web.Response(text=self.settings.CONF_CODE)

        obj = data["object"]

        if "user_id" in obj:
            obj['user_id'] = int(obj['user_id'])

        if data_type == 'message_new':
            data = MessageEventData.from_message_body(obj)

            msg = Message(self.api, data)

            await self.process_message(msg)

        else:
            evnt = CallbackEvent(self.api, data_type, obj)
            await self.process_event(evnt)

        return web.Response(text="ok")

    def longpoll_run(self, custom_process=False):
        self.main_task = Task(self.longpoll_processor())

        if custom_process:
            return self.main_task

        self.logger.info("Started to process messages")

        try:
            self.loop.run_until_complete(self.main_task)

        except (KeyboardInterrupt, SystemExit):
            self.stop()

            self.logger.info("Stopped to process messages")

        except asyncio.CancelledError:
            pass

    def callback_run(self, custom_process=False):
        host = getenv('IP', '127.0.0.1')
        port = int(getenv('PORT', 8000))

        self.logger.info("Started to process messages")

        try:
            server_generator, handler, app = self.loop.run_until_complete(self.init_app(host, port, self.loop))
            server = self.loop.run_until_complete(server_generator)
        except OSError:
            self.logger.error("Address already in use: " + str(host) + ":" + str(port))
            return

        self.main_task = Future()

        if custom_process:
            return self.main_task

        print("======== Running on http://{}:{} ========\n"
              "         (Press CTRL+C to quit)".format(*server.sockets[0].getsockname()))

        def stop_server():
            server.close()

            if not self.loop.is_running():
                return

            self.loop.run_until_complete(server.wait_closed())
            self.loop.run_until_complete(app.shutdown())
            self.loop.run_until_complete(handler.shutdown(10))
            self.loop.run_until_complete(app.cleanup())

        try:
            self.loop.run_until_complete(self.main_task)
        except KeyboardInterrupt:
            self.stop()

            stop_server()

            self.loop.close()

        except asyncio.CancelledError:
            pass

        finally:
            stop_server()

            self.logger.info("Stopped to process messages")

    async def init_app(self, host, port, loop):
        app = web.Application()
        app.router.add_post('/', self.callback_processor)

        handler = app.make_handler()

        server_generator = loop.create_server(handler, host, port)
        return server_generator, handler, app

    def stop_bot(self, full=False):
        try:
            if self.main_task:
                self.main_task.cancel()
        except Exception:
            import traceback
            traceback.print_exc()

        if full:
            self.stop()
            self.loop.stop()

        self.logger.info("Attempting to turn bot off")

    async def process_message(self, msg):
        asyncio.ensure_future(self.handler.process(msg), loop=self.loop)

    async def check_event(self, user_id, chat_id, attaches):
        if chat_id != 0 and "source_act" in attaches:
            photo = attaches.get("attach1_type") + attaches.get("attach1") if "attach1" in attaches else None

            evnt = ChatChangeEvent(self.api, user_id, chat_id, attaches.get("source_act"),
                                   int(attaches.get("source_mid", 0)), attaches.get("source_text"),
                                   attaches.get("source_old_text"), photo, int(attaches.get("from", 0)))

            await self.process_event(evnt)

            return True

        return False

    async def process_event(self, evnt):
        asyncio.ensure_future(self.handler.process_event(evnt), loop=self.loop)

    def do(self, coroutine):
        if asyncio.iscoroutine(coroutine):
            return self.loop.run_until_complete(coroutine)

        return False

    @staticmethod
    def silent(func):
        try:
            func()
        except Exception as e:
            print(e)

    def stop(self):
        self.handler.stop()
        self.api.stop()

        self.silent(self.main_task.cancel)

        self.logger.removeHandler(self.logger_file)
        self.logger_file.close()


if __name__ == "__main__":
    try:
        import sys

        if "-d" in sys.argv:
            raise ModuleNotFoundError

        from settings_real import BotSettings

    except ModuleNotFoundError:
        from settings import BotSettings

    except ImportError:
        import traceback
        traceback.print_exc()
        exit(1)

    bot = Bot(BotSettings)
    bot.longpoll_run()
    # bot.callback_run()
