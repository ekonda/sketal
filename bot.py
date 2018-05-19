import asyncio, aiohttp, json, time, logging

from asyncio import Future, Task
from aiohttp import web
from os import getenv

from handler.handler_controller import MessageHandler
from utils import parse_msg_flags

from utils import VkController
from utils import Message, LongpollEvent, ChatChangeEvent, CallbackEvent
from utils import MessageEventData


class Bot:
    __slots__ = (
        "api", "handler", "logger", "logger_file", "loop",
        "tasks", "sessions", "requests", "settings"
    )

    def __init__(self, settings, logger=None, handler=None, loop=None):
        self.settings = settings

        if logger:
            self.logger = logger
        else:
            self.logger = self.init_logger()

        if loop:
            self.loop = loop
        else:
            self.loop = asyncio.get_event_loop()

        self.logger.info("Initializing bot")

        self.requests = []
        self.sessions = []
        self.tasks = []

        self.logger.info("Initializing vk clients")
        self.api = VkController(settings, logger=self.logger, loop=self.loop)

        self.logger.info("Loading plugins")
        if handler:
            self.handler = handler

        else:
            self.handler = MessageHandler(self, self.api, initiate_plugins=False)
            self.handler.initiate_plugins()

        self.logger.info("Bot successfully initialized")

    def init_logger(self):
        logger = logging.Logger("sketal", level=logging.DEBUG if self.settings.DEBUG else logging.INFO)

        formatter = logging.Formatter(
            fmt=u'[%(asctime)s] %(levelname)-8s: %(message)s',
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

        return logger

    def add_task(self, task):
        for ctask in self.tasks[::]:
            if ctask.done() or ctask.cancelled():
                self.tasks.remove(ctask)

        if task.done() or task.cancelled():
            return

        self.tasks.append(task)

        return task

    async def init_long_polling(self, pack, update=0):
        result = None

        for _ in range(4):
            result = await self.api(sender=self.api.target_client). \
                messages.getLongPollServer(use_ssl=1, lp_version=2)

            if result:
                break

            time.sleep(0.5)

        if not result:
            self.logger.error("Unable to connect to VK's long polling server.")
            exit()

        if update == 0:
            pack[1] = "https://" + result['server']
            pack[0]['key'] = result['key']
            pack[0]['ts'] = result['ts']

        elif update == 2:
            pack[0]['key'] = result['key']

        elif update == 3:
            pack[0]['key'] = result['key']
            pack[0]['ts'] = result['ts']

    async def init_bots_long_polling(self, pack, update=0):
        result = None

        for _ in range(4):
            result = await self.api(sender=self.api.target_client).\
                groups.getLongPollServer(group_id=self.api.get_current_id())

            if result:
                break

            time.sleep(0.5)

        if not result:
            self.logger.error("Unable to connect to VK's bots long polling server.")
            exit()

        if update == 0:
            pack[1] = result['server']
            pack[0]['key'] = result['key']
            pack[0]['ts'] = result['ts']

        elif update == 2:
            pack[0]['key'] = result['key']

        elif update == 3:
            pack[0]['key'] = result['key']
            pack[0]['ts'] = result['ts']

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

        if 'from' in data.attaches and len(new_event) > 3:
            data.user_id = int(data.attaches.pop('from'))
            data.chat_id = int(new_event[3]) - 2000000000
            data.is_multichat = True

        else:
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
            data.forwarded = MessageEventData.\
                parse_brief_forwarded_messages_from_lp(data.attaches.pop("fwd"))

        else:
            data.forwarded = []

        msg = Message(self.api, data)

        if await self.check_event(data.user_id, data.chat_id, data.attaches):
            msg.is_event = True

        await self.process_message(msg)

    async def longpoll_processor(self):
        pack = [{'act': 'a_check', 'key': '', 'ts': 0, 'wait': 25, 'mode': 10,
            'version': 2}, ""]

        await self.init_long_polling(pack)

        session = aiohttp.ClientSession(loop=self.loop)
        self.sessions.append(session)

        while True:
            try:
                requ = session.get(pack[1], params=pack[0])
            except aiohttp.ClientOSError:
                await asyncio.sleep(0.5)
                continue

            self.requests.append(requ)

            try:
                events = json.loads(await (await requ).text())

            except aiohttp.ClientOSError:
                try:
                    self.sessions.remove(session)
                except ValueError:
                    pass

                await asyncio.sleep(0.5)

                session = aiohttp.ClientSession(loop=self.loop)
                self.sessions.append(session)
                continue

            except (asyncio.TimeoutError, aiohttp.ServerDisconnectedError):
                self.logger.warning("Long polling server doesn't respond. Changing server.")

                await asyncio.sleep(0.5)

                await self.init_long_polling(pack)
                continue

            except ValueError:
                await asyncio.sleep(0.5)
                continue

            finally:
                if requ in self.requests:
                    self.requests.remove(requ)

            failed = events.get('failed')

            if failed:
                err_num = int(failed)

                if err_num == 1:  # 1 - update timestamp
                    if 'ts' not in events:
                        await self.init_long_polling(pack)
                    else:
                        pack[0]['ts'] = events['ts']

                elif err_num in (2, 3):  # 2, 3 - new data for long polling
                    await self.init_long_polling(pack, err_num)

                continue

            pack[0]['ts'] = events['ts']

            for event in events['updates']:
                asyncio.ensure_future(self.process_longpoll_event(event))

    async def bots_longpoll_processor(self):
        pack = [{'act': 'a_check', 'key': '', 'ts': 0,
            'wait': 25}, ""]

        await self.init_bots_long_polling(pack)

        session = aiohttp.ClientSession(loop=self.loop)
        self.sessions.append(session)

        while True:
            try:
                requ = session.get(pack[1], params=pack[0])
            except aiohttp.ClientOSError:
                await asyncio.sleep(0.5)
                continue

            self.requests.append(requ)

            try:
                events = json.loads(await (await requ).text())

            except aiohttp.ClientOSError:
                try:
                    self.sessions.remove(session)
                except ValueError:
                    pass

                await asyncio.sleep(0.5)

                session = aiohttp.ClientSession(loop=self.loop)
                self.sessions.append(session)
                continue

            except (asyncio.TimeoutError, aiohttp.ServerDisconnectedError):
                self.logger.warning("Long polling server doesn't respond. Changing server.")
                await asyncio.sleep(0.5)

                await self.init_bots_long_polling(pack)
                continue

            except ValueError:
                await asyncio.sleep(0.5)
                continue

            finally:
                if requ in self.requests:
                    self.requests.remove(requ)

            failed = events.get('failed')

            if failed:
                err_num = int(failed)

                if err_num == 1:  # 1 - update timestamp
                    if 'ts' not in events:
                        await self.init_bots_long_polling(pack)
                    else:
                        pack[0]['ts'] = events['ts']

                elif err_num in (2, 3):  # 2, 3 - new data for long polling
                    await self.init_bots_long_polling(pack, err_num)

                continue

            pack[0]['ts'] = events['ts']

            for event in events['updates']:
                if "type" not in event or "object" not in event:
                    continue

                data_type = event["type"]
                obj = event["object"]

                if "user_id" in obj:
                    obj['user_id'] = int(obj['user_id'])

                if data_type == 'message_new':
                    await self.process_message(
                        Message(self.api, MessageEventData.from_message_body(obj)))

                else:
                    await self.process_event(
                        CallbackEvent(self.api, data_type, obj))

    async def callback_processor(self, request):
        try:
            data = await request.json()

            if "type" not in data or "object" not in data:
                raise ValueError("Damaged data received.")

        except (UnicodeDecodeError, ValueError):
            return web.Response(text="ok")

        data_type = data["type"]

        if data_type == "confirmation":
            return web.Response(text=self.settings.CONF_CODE)

        obj = data["object"]

        if "user_id" in obj:
            obj['user_id'] = int(obj['user_id'])

        if data_type == 'message_new':
            await self.process_message(
                Message(self.api, MessageEventData.from_message_body(obj)))

        else:
            await self.process_event(
                CallbackEvent(self.api, data_type, obj))

        return web.Response(text="ok")

    def longpoll_run(self, custom_process=False):
        task = self.add_task(Task(self.longpoll_processor()))

        if custom_process:
            return task

        self.logger.info("Started to process messages")

        try:
            self.loop.run_until_complete(task)

        except (KeyboardInterrupt, SystemExit):
            self.loop.run_until_complete(self.stop())

        except asyncio.CancelledError:
            pass

    def bots_longpoll_run(self, custom_process=False):
        task = self.add_task(Task(self.bots_longpoll_processor()))

        if custom_process:
            return task

        self.logger.info("Started to process messages")

        try:
            self.loop.run_until_complete(task)

        except (KeyboardInterrupt, SystemExit):
            self.loop.run_until_complete(self.stop())

        except asyncio.CancelledError:
            pass

    def callback_run(self, custom_process=False):
        host = getenv('IP', '127.0.0.1')
        port = int(getenv('PORT', 8000))

        self.logger.info("Started to process messages")

        try:
            app = web.Application()
            app.router.add_post('/', self.callback_processor)

            runner = web.AppRunner(app)
            self.loop.run_until_complete(runner.setup())

            site = web.TCPSite(runner, host, port)
            self.loop.run_until_complete(site.start())

        except OSError:
            self.logger.error("Address already in use: " + str(host) + ":" + str(port))
            return

        task = self.add_task(Future())

        if custom_process:
            return task

        print("======== Running on http://{}:{} ========\n"
              "         (Press CTRL+C to quit)".format(*server.sockets[0].getsockname()))

        try:
            self.loop.run_until_complete(task)

        except (KeyboardInterrupt, SystemExit):
            self.loop.run_until_complete(runner.cleanup())
            self.loop.run_until_complete(self.stop())

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

    def coroutine_exec(self, coroutine):
        if asyncio.iscoroutine(coroutine) or isinstance(coroutine, asyncio.Future):
            return self.loop.run_until_complete(coroutine)

        return False

    async def stop_tasks(self):
        self.logger.info("Attempting stop bot")

        for task in self.tasks:
            try:
                task.cancel()
            except Exception:
                pass

        self.logger.info("Stopped to process messages")

    async def stop(self):
        self.logger.info("Attempting to turn bot off")

        for session in self.sessions:
            await session.close()

        await self.handler.stop()
        await self.api.stop()

        for task in self.tasks:
            try:
                task.cancel()
            except Exception:
                pass

        self.logger.removeHandler(self.logger_file)
        self.logger_file.close()

        self.logger.info("Stopped to process messages")
