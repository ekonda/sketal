import sys, os
sys.path.append(os.path.abspath("."))

import asyncio, unittest, logging, types, time

from bot import Bot
from plugins import *
from skevk import *
from utils import *

try:
    from settings_prod import BotSettings

except ImportError:
    from settings import BotSettings
    BotSettings.USERS = ()

# Install tokens for tests if provided
test_group_token = os.environ.get('SKETAL_GROUP_TOKEN', '')
if test_group_token and not os.environ.get('SKETAL_GROUP_IGNORE', 0):
    BotSettings.USERS += (
        ("group", test_group_token,),
    )

test_user_token = os.environ.get('SKETAL_USER_TOKEN', '')
if test_user_token and not os.environ.get('SKETAL_USER_IGNORE', 0):
    BotSettings.USERS += (
        ("user", test_user_token,),
    )

# Install required plugins for tests
required = [AntifloodPlugin, TimePlugin]
for p in BotSettings.PLUGINS[::]:
    for r in required[::]:
        if isinstance(p, r):
            required.remove(r)
for r in required:
    BotSettings.PLUGINS = BotSettings.PLUGINS + r()

# BotSettings.DEBUG = True

class TestSketal(unittest.TestCase):
    # def setUp(self):
    #     self.startTime = time.time()
    #
    # def tearDown(self):
    #     t = time.time() - self.startTime
    #     print("%s: %.3f" % (self.id(), t))

    @classmethod
    def setUpClass(cls):
        cls.bot = Bot(BotSettings)
        cls.user_id = cls.bot.api.get_current_id()

    def test_loading(self):
        logger = logging.getLogger()

        with self.assertLogs(logger, level='INFO') as cm:
            self.bot = Bot(BotSettings, logger=logger)

        self.assertIn(f'INFO:{self.bot.logger.name}:Initializing bot', cm.output)
        self.assertIn(f'INFO:{self.bot.logger.name}:Initializing vk clients', cm.output)
        self.assertIn(f'INFO:{self.bot.logger.name}:Loading plugins', cm.output)

    def test_process(self):
        m = Message(self.bot.api, MessageEventData.from_message_body({
            "id": 1, "date": 0,
            "user_id": self.user_id,
            "body": "Привет! Просто сообщение.",
            "random_id": 0, "read_state": 1, "title": "", "out": 0
        }))

        self.bot.do(self.bot.handler.process(m))

    def test_plugins(self):
        """Requires TimePlugin and AntifloodPlugin."""

        messages = []

        _answer = Message.answer
        async def answer(self, text="", **kwargs):
            messages.insert(0, text)
        Message.answer = answer

        m = Message(self.bot.api, MessageEventData.from_message_body({
            "id": 1,
            "date": 0,
            "user_id": self.user_id,
            "body": "/время",
            "random_id": 0, "read_state": 1, "title": "", "out": 0
        }))

        self.bot.do(self.bot.handler.process(m))

        self.assertIn("Текущие дата и время по МСК", messages[0])

        self.bot.do(self.bot.handler.process(m))

        self.assertEqual(len(messages), 1)

        Message.answer = _answer

    def test_methods(self):
        """Requires at least 1 message in dialogs on account."""

        result = self.bot.do(self.bot.api.groups.getById(group_id=1))
        self.assertNotIn(result, (False, None))

        count = 2
        result = self.bot.do(self.bot.api.messages.get(count=count))
        self.assertNotIn(result, (False, None))
        self.assertIn("items", result)
        self.assertEqual(len(result['items']), count)

        result = self.bot.do(self.bot.api(wait=Wait.CUSTOM).messages.get(count=1))
        self.assertEqual(asyncio.isfuture(result), True)
        self.bot.loop.run_until_complete(result)
        self.assertEqual(result.done(), True)
        self.assertNotIn(result.result(), (False, None))

    def test_longpoll(self):
        task = self.bot.longpoll_run(True)

        async def bot_stopper():
            await asyncio.sleep(1.5)
            self.bot.stop_bot()

        asyncio.ensure_future(bot_stopper(), loop=self.bot.loop)

        with self.assertLogs(self.bot.logger, level='INFO') as cm:
            with self.assertRaises(asyncio.CancelledError):
                self.bot.loop.run_until_complete(task)

        self.assertEqual(cm.output, [f'INFO:{self.bot.logger.name}:Attempting to turn bot off'])

    def test_bots_longpoll(self):
        if all("group" not in e for e in self.bot.settings.USERS):
            return

        task = self.bot.bots_longpoll_run(True)

        async def bot_stopper():
            await asyncio.sleep(1.5)
            self.bot.stop_bot()

        asyncio.ensure_future(bot_stopper(), loop=self.bot.loop)

        with self.assertLogs(self.bot.logger, level='INFO') as cm:
            with self.assertRaises(asyncio.CancelledError):
                self.bot.loop.run_until_complete(task)

        self.assertEqual(cm.output, [f'INFO:{self.bot.logger.name}:Attempting to turn bot off'])

    def test_callback(self):
        task = self.bot.callback_run(True)

        async def bot_stopper():
            await asyncio.sleep(1.5)
            self.bot.stop_bot()

        asyncio.ensure_future(bot_stopper(), loop=self.bot.loop)

        with self.assertLogs(self.bot.logger, level='INFO') as cm:
            with self.assertRaises(asyncio.CancelledError):
                self.bot.loop.run_until_complete(task)

        self.assertEqual(cm.output, [f'INFO:{self.bot.logger.name}:Attempting to turn bot off'])

    def test_errors(self):
        with self.assertLogs(self.bot.logger, level='ERROR') as cm:
            self.bot.do(self.bot.api.messages.send())

        self.assertIn(r"ERROR:sketal:Errors while executing vk method: {'code': 100, 'method': 'messages.send', 'error_msg': 'One of the parameters specified was missing or invalid: you should specify peer_id, user_id, domain, chat_id or user_ids param'}, {'code': 100, 'method': 'execute', 'error_msg': 'One of the parameters specified was missing or invalid: you should specify peer_id, user_id, domain, chat_id or user_ids param'}", cm.output)

    def test_upload(self):
        with open("tests/simple_image.png", "rb") as f:
            image = f.read()

            res_photo, res_doc = self.bot.do(
                asyncio.gather(
                    upload_photo(self.bot.api, image),
                    upload_doc(self.bot.api, image, "image.png")
                )
            )

        self.assertIsNotNone(res_photo)
        self.assertIsNotNone(res_doc)
        self.assertNotEqual(res_photo.url, "")
        self.assertNotEqual(res_doc.url, "")

        self.bot.do(
            asyncio.gather(
                self.bot.api.photos.delete(owner_id=res_photo.owner_id,
                    photo_id=res_photo.id),
                self.bot.api.docs.delete(owner_id=res_doc.owner_id,
                    doc_id=res_doc.id)
            )
        )

    def test_accumulative_methods(self):
        async def work():
            sender = self.bot.api.get_default_sender("wall.getById")

            tas1 = await self.bot.api.method_accumulative("wall.getById", {},
                {"posts": "-145935681_515"}, sender=sender, wait=Wait.CUSTOM)
            tas2 = await self.bot.api.method_accumulative("wall.getById", {},
                {"posts": "-145935681_512"}, sender=sender, wait=Wait.CUSTOM)
            tas3 = await self.bot.api.method_accumulative("wall.getById", {},
                {"posts": "-145935681_511"}, sender=sender, wait=Wait.CUSTOM)

            await asyncio.gather(tas1, tas2, tas3, loop=self.bot.loop,
                return_exceptions=True)

            self.assertEqual(tas1.result()["id"], 515)
            self.assertEqual(tas2.result()["id"], 512)
            self.assertEqual(tas3.result()["id"], 511)

        self.bot.do(work())

class TestSketalUtils(unittest.TestCase):
    def check(self, message):
        self.assertLessEqual(len(message), MAX_LENGHT)
        self.assertGreaterEqual(len(message), 1)

    def test_json_iter_parse(self):
        self.assertEqual(
            list(json_iter_parse('{"a": 1, "b": 2}{"c": 3, "d": 4}')),
            [{"a": 1, "b": 2}, {"c": 3, "d": 4}]
        )

    def test_parse_msg_flags(self):
        a = parse_msg_flags(2)
        self.assertTrue(a['outbox'])
        self.assertFalse(a['unread'])
        self.assertFalse(a['hidden'])

        a = parse_msg_flags(3)
        self.assertTrue(a['unread'])
        self.assertTrue(a['outbox'])
        self.assertFalse(a['hidden'])

    def test_traverse(self):
        a = [10, 20, [10, 20, [10, 20]]]
        self.assertEqual(list(traverse(a)), [10, 20, 10, 20, 10, 20])

        b = [50, [40, 30]]
        self.assertEqual(list(traverse(b)), [50, 40, 30])

    def test_plural_form(self):
        words = ("корова", "коровы", "коров")

        self.assertEqual(plural_form(2, words), "2 коровы")
        self.assertEqual(plural_form(25, words), "25 коров")
        self.assertEqual(plural_form(21, words), "21 корова")
        self.assertEqual(plural_form(12, words), "12 коров")
        self.assertEqual(plural_form(100, words), "100 коров")
        self.assertEqual(plural_form(51234, words), "51234 коровы")

    def test_simple_message(self):
        result = Message.prepare_message("hi")

        size = 0
        for r in result:
            self.check(r)
            size += 1

        self.assertEqual(size, 1)

    def test_long_messages(self):
        result = Message.prepare_message("a" * MAX_LENGHT)
        for r in result:
            self.check(r)

        result = Message.prepare_message(("a" * (MAX_LENGHT - 1) + "\n") * 2)
        for r in result:
            self.check(r)

        result = Message.prepare_message(("a" * MAX_LENGHT + "\n") * 2)
        for r in result:
            self.check(r)

    def test_bad_messages(self):
        result = list(Message.prepare_message("a\n" * (MAX_LENGHT // 2)))

        for r in result:
            self.check(r)

        self.assertEqual(len(result), 1)

        result = Message.prepare_message("a" * (MAX_LENGHT * 3))

        for r in result:
            self.check(r)

        result = list(Message.prepare_message("a " * int(MAX_LENGHT * 2.9)))

        for r in result:
            self.check(r)

        self.assertEqual(len(result), 6)

        result = list(Message.prepare_message("a" * MAX_LENGHT + " a"))

        for r in result:
            self.check(r)

        self.assertEqual(len(result), 2)
        self.assertEqual(len(result[-1]), 1)

        result = list(Message.prepare_message("a" * MAX_LENGHT + " aaaa"))

        for r in result:
            self.check(r)

        self.assertEqual(len(result), 2)
        self.assertEqual(len(result[-1]), 4)


class TestSketalPlugins(unittest.TestCase):
    pass  # Currently no tests here


if __name__ == '__main__':
    unittest.main()
