import sys, os
sys.path.append(os.path.abspath("."))

import asyncio, unittest, logging, time


# Optimize testing
import utils

async def parse_user_name(user_id, entity):
    return str(user_id)

async def parse_user_id(msg, can_be_argument=True, argument_ind=-1, custom_text=None):
    text = msg.text.split(" ")[argument_ind]

    if text.isdigit():
        return int(text)

    if text.startswith("https://vk.com/"):
        text = text[15:]

    if text[:3] == "[id":
        puid = text[3:].split("|")[0]

        if puid.isdigit() and "]" in text[3:]:
            return int(puid)

utils.parse_user_name = parse_user_name
utils.parse_user_id = parse_user_id
# ----------------


from bot import Bot
from plugins import *
from utils import *

from settings_base import BaseSettings

try:
    from settings_prod import BotSettings
except ImportError:
    from settings import BotSettings
    BotSettings.USERS = ()

# BotSettings.DEBUG = True

# Install tokens for tests if provided
test_group_token = os.environ.get('SKETAL_GROUP_TOKEN', '')
if test_group_token and not int(os.environ.get('SKETAL_GROUP_IGNORE', 0)):
    BotSettings.USERS += (
        ("group", test_group_token,),
    )

test_user_token = os.environ.get('SKETAL_USER_TOKEN', '')
if test_user_token and not int(os.environ.get('SKETAL_USER_IGNORE', 0)):
    BotSettings.USERS += (
        ("user", test_user_token,),
    )

class TestSketal(unittest.TestCase):
    # def setUp(self):
    #     self.startTime = time.time()
    #
    # def tearDown(self):
    #     t = time.time() - self.startTime
    #     print("%s: %.3f" % (self.id(), t))

    @classmethod
    def setUpClass(cls):
        required = [AntifloodPlugin, TimePlugin]

        for p in BotSettings.PLUGINS[::]:
            for r in required[::]:
                if isinstance(p, r):
                    required.remove(r)

        for r in required:
            BotSettings.PLUGINS = BotSettings.PLUGINS + r()

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

        self.bot.coroutine_exec(self.bot.handler.process(m))

    def test_plugins(self):
        """Requires TimePlugin and AntifloodPlugin."""

        messages = []

        _answer = Message.answer
        async def answer(self, message="", **kwargs):
            messages.append(message)
        Message.answer = answer

        m = Message(self.bot.api, MessageEventData.from_message_body({
            "id": 1,
            "date": 0,
            "user_id": self.user_id,
            "body": "/время",
            "random_id": 0, "read_state": 1, "title": "", "out": 0
        }))

        self.bot.coroutine_exec(self.bot.handler.process(m))

        self.assertIn("Текущие дата и время по МСК", messages[0])

        self.bot.coroutine_exec(self.bot.handler.process(m))

        self.assertEqual(len(messages), 1)

        Message.answer = _answer

    def test_bots_longpoll(self):
        if all("group" not in e for e in self.bot.settings.USERS):
            return

        task = self.bot.bots_longpoll_run(True)

        async def bot_stopper():
            await asyncio.sleep(1.5)
            await self.bot.stop_tasks()

        asyncio.ensure_future(bot_stopper(), loop=self.bot.loop)

        with self.assertLogs(self.bot.logger, level='INFO') as cm:
            with self.assertRaises(asyncio.CancelledError):
                self.bot.loop.run_until_complete(task)

        self.assertEqual(cm.output, [f"INFO:{self.bot.logger.name}:Attempting stop bot", f"INFO:{self.bot.logger.name}:Stopped to process messages"])

    def test_callback(self):
        task = self.bot.callback_run(True)

        async def bot_stopper():
            await asyncio.sleep(1.5)
            await self.bot.stop_tasks()

        asyncio.ensure_future(bot_stopper(), loop=self.bot.loop)

        with self.assertLogs(self.bot.logger, level='INFO') as cm:
            with self.assertRaises(asyncio.CancelledError):
                self.bot.loop.run_until_complete(task)

        self.assertEqual(cm.output, [f"INFO:{self.bot.logger.name}:Attempting stop bot", f"INFO:{self.bot.logger.name}:Stopped to process messages"])

    def test_errors(self):
        with self.assertLogs(self.bot.logger, level='ERROR') as cm:
            self.bot.coroutine_exec(self.bot.api.messages.send())

        full_error_text = "\n".join(cm.output)

        self.assertIn("Errors while executing vk method", full_error_text)
        self.assertIn("'error_code': 100", full_error_text)
        self.assertIn("One of the parameters specified was missing or invalid", full_error_text)

    def test_upload(self):
        with open("tests/simple_image.png", "rb") as f:
            image = f.read()

            res_photo, res_doc = self.bot.coroutine_exec(
                asyncio.gather(
                    upload_photo(self.bot.api, image),
                    upload_doc(self.bot.api, image, "image.png")
                )
            )

        self.assertIsNotNone(res_photo)
        self.assertIsNotNone(res_doc)
        self.assertNotEqual(res_photo.url, "")
        self.assertNotEqual(res_doc.url, "")

        self.bot.coroutine_exec(
            asyncio.gather(
                self.bot.api.photos.delete(owner_id=res_photo.owner_id,
                    photo_id=res_photo.id),
                self.bot.api.docs.delete(owner_id=res_doc.owner_id,
                    doc_id=res_doc.id)
            )
        )

    def test_accumulative_methods(self):
        if int(os.environ.get('SKETAL_USER_IGNORE', 0)):
            return

        async def work():
            sender = self.bot.api.get_default_sender("wall.getById")

            tas1 = await self.bot.api.method_accumulative("wall.getById", {},
                {"posts": "-145935681_515"}, sender=sender, wait="custom")
            tas2 = await self.bot.api.method_accumulative("wall.getById", {},
                {"posts": "-145935681_512"}, sender=sender, wait="custom")
            tas3 = await self.bot.api.method_accumulative("wall.getById", {},
                {"posts": "-145935681_511"}, sender=sender, wait="custom")

            await asyncio.gather(tas1, tas2, tas3, loop=self.bot.loop,
                return_exceptions=True)

            self.assertEqual(tas1.result()["id"], 515)
            self.assertEqual(tas2.result()["id"], 512)
            self.assertEqual(tas3.result()["id"], 511)

        self.bot.coroutine_exec(work())

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
    """Some amount of testing."""

    @classmethod
    def setUpClass(cls):
        DEFAULTS["ADMINS"] = BaseSettings.DEFAULT_ADMINS
        BotSettings.DEFAULT_ADMINS = BaseSettings.DEFAULT_ADMINS

        BotSettings.PLUGINS = (
            StoragePlugin(in_memory=True), CalculatorPlugin(),
            StaffControlPlugin(admins=(2,), set_admins=True), AboutPlugin(),
            TimePlugin(), NoQueuePlugin(), ChatControlPlugin(banned=(100,)),
        )

        cls.bot = Bot(BotSettings)
        cls.user_id = cls.bot.api.get_current_id()

        cls._answer = Message.answer
        cls.messages = []

        async def answer(self, message="", **kwargs):
            cls.messages.append(message)

        Message.answer = answer

    @classmethod
    def tearDownClass(cls):
        Message.answer = cls._answer

    def tearDown(self):
        self.messages.clear()

    def message(self, text, chat=False, admin=False):
        if chat:
            return Message(self.bot.api, MessageEventData.from_message_body({
                "id": 1,
                "date": 0,
                "user_id": 2 if admin else 1,
                "chat_id": chat,
                "body": text,
                "title": "Тестик",
                "random_id": 0, "read_state": 1, "out": 0
            }))

        return Message(self.bot.api, MessageEventData.from_message_body({
            "id": 1,
            "date": 0,
            "user_id": 2 if admin else 1,
            "body": text,
            "random_id": 0, "read_state": 1, "title": "", "out": 0
        }))

    def process(self, text, chat=False, admin=False):
        self.bot.coroutine_exec(self.bot.handler.process(self.message(text, chat, admin)))

    def test_about_plugin(self):
        self.process("/о боте")
        self.process("/о боте")

        self.assertEqual(self.messages[0], self.messages[1])
        self.assertIn("https://github.com/vk-brain/sketal", self.messages[0])

    def test_chat_control_plugin(self):
        self.process("/беседа", 50)
        self.process("/беседа")
        self.process("/беседа инфо", 50)

        self.assertEqual(self.messages, [])

        self.process("/беседа техинфо")
        self.assertIn(" не беседа", self.messages[0])

        self.process("/беседа техинфо", 50, True)
        self.assertIn(" #50", self.messages[1])

        self.process("/беседа техинфо", 100, True)
        self.assertEqual(len(self.messages), 2)

        self.process("/беседа бан 99", 50)
        self.assertIn(" недостаточно прав", self.messages[2])

        self.process("/беседа разбан 100", 50)
        self.assertIn(" недостаточно прав", self.messages[3])

        self.process("/беседа разбан 100", 50, True)
        self.assertIn(" #100 разблокирована", self.messages[4])

        self.process("/беседа техинфо", 100, True)
        self.assertIn(" #100", self.messages[5])

        self.process("/беседа бан 100", 100, True)
        self.assertIn(" #100 заблокирована", self.messages[6])

    def test_control_plugin(self):
        self.process("/контроль")
        self.process("/контроль список админов")
        self.process("/контроль список модеров")
        self.process("/контроль список банов")
        self.process("/контроль список випов")
        self.process("/контроль добавить админа 100")
        self.process("/контроль добавить модера 50")
        self.process("/контроль добавить вип 10")
        self.process("/контроль добавить бан 1")

        self.assertEqual(len(self.messages), 9)
        self.assertIn("Администрационные команды", self.messages[0])

        self.assertEqual(self.messages[1].count("👆"), 1)

        for message in self.messages[2:5]:
            self.assertIn("Никого нет", message)

        for message in self.messages[-4:]:
            self.assertIn("недостаточно прав", message)

        self.process("/контроль добавить админа 3", admin=True)
        self.process("/контроль добавить модера 4", 51, admin=True)
        self.process("/контроль добавить вип 5", admin=True)
        self.process("/контроль добавить бан 6", admin=True)

        self.process("/контроль список админов")
        self.assertEqual(self.messages[13].count("👆"), 2)
        self.process("/контроль список модеров", 51)
        self.assertEqual(self.messages[14].count("👉"), 1)
        self.process("/контроль список випов")
        self.assertEqual(self.messages[15].count("👻"), 1)
        self.process("/контроль список банов")
        self.assertEqual(self.messages[16].count("👺"), 1)

        self.process("/контроль убрать админа 3", admin=True)
        self.process("/контроль убрать модера 4", 51, admin=True)
        self.process("/контроль убрать вип 5", admin=True)
        self.process("/контроль убрать бан 6", admin=True)

        self.process("/контроль список админов")
        self.assertEqual(self.messages[21].count("👆"), 1)
        self.process("/контроль список модеров")
        self.assertEqual(self.messages[22].count("👉"), 0)
        self.process("/контроль список випов")
        self.assertEqual(self.messages[23].count("👻"), 0)
        self.process("/контроль список банов")
        self.assertEqual(self.messages[24].count("👺"), 0)

if __name__ == '__main__':
    unittest.main()
