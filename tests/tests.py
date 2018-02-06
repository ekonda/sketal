import sys, os
sys.path.append(os.path.abspath("."))

import unittest

from bot import Bot

from vk.plus import asyncio, Wait
from vk.data import Message, MAX_LENGHT
from vk.helpers import upload_doc, upload_photo

try:
    from settings_real import BotSettings
except ImportError:
    from settings import BotSettings

user_token = os.environ.get('SKETAL_USER_TOKEN', '')
if user_token:
    BotSettings.USERS = (
        ("user", user_token,),
    )

class TestBot(unittest.TestCase):
    bot = Bot(BotSettings)

    def test_loading(self):
        with self.assertLogs(self.bot.logger, level='INFO') as cm:
            self.bot = Bot(BotSettings, logger=self.bot.logger)

        self.assertIn(f'INFO:{self.bot.logger.name}:Initializing bot', cm.output)
        self.assertIn(f'INFO:{self.bot.logger.name}:Initializing vk clients', cm.output)
        self.assertIn(f'INFO:{self.bot.logger.name}:Loading plugins', cm.output)

    def test_methods(self):
        result = self.bot.do(self.bot.api.groups.getById(group_id=1))
        self.assertNotIn(result, (False, None))

        count = 4
        result = self.bot.do(self.bot.api.messages.get(count=count))
        self.assertNotIn(result, (False, None))
        self.assertIn("items", result)
        self.assertEqual(len(result['items']), count)

        result = self.bot.do(self.bot.api().messages.get(count=1))
        self.assertNotIn(result, (False, None))

        result = self.bot.do(self.bot.api(wait=Wait.CUSTOM).messages.get(count=1))
        self.assertEqual(asyncio.isfuture(result), True)
        self.bot.loop.run_until_complete(result)
        self.assertEqual(result.done(), True)
        self.assertNotIn(result.result(), (False, None))

    def test_longpoll(self):
        task = self.bot.longpoll_run(True)

        async def bot_killer():
            await asyncio.sleep(5)
            self.bot.stop_bot()

        asyncio.ensure_future(bot_killer(), loop=self.bot.loop)

        with self.assertLogs(self.bot.logger, level='INFO') as cm:
            with self.assertRaises(asyncio.CancelledError):
                self.bot.loop.run_until_complete(task)

        self.assertEqual(cm.output, [f'INFO:{self.bot.logger.name}:Attempting to turn bot off'])

    def test_callback(self):
        task = self.bot.callback_run(True)

        async def bot_killer():
            await asyncio.sleep(5)
            self.bot.stop_bot()

        asyncio.ensure_future(bot_killer(), loop=self.bot.loop)

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
            result = self.bot.do(upload_photo(self.bot.api, f.read()))

        self.assertIsNotNone(result)
        self.assertNotEqual(result.url, "")

        self.bot.do(self.bot.api.photos.delete(owner_id=result.owner_id, photo_id=result.id))

        with open("tests/simple_image.png", "rb") as f:
            result = self.bot.do(upload_doc(self.bot.api, f.read(), "image.png"))

        self.assertIsNotNone(result)
        self.assertNotEqual(result.url, "")

        self.bot.do(self.bot.api.docs.delete(owner_id=result.owner_id, doc_id=result.id))

    def test_mass_method(self):
        async def work():
            with self.bot.api.mass_request():
                tasks = []

                for _ in range(70):
                    tasks.append(await self.bot.api(wait=Wait.CUSTOM).messages.get(count=1))

                while tasks:
                    await asyncio.sleep(0.01)

                    task = tasks.pop()

                    if task.done():
                        continue

                    tasks.append(task)

        self.bot.do(work())

    def test_accumulative_methods(self):
        async def work():
            sender = self.bot.api.get_default_sender("wall.getById")

            with self.bot.api.mass_request():
                tas1 = await self.bot.api.method_accumulative("wall.getById", {}, {"posts": "-145935681_515"},
                                                              sender=sender, wait=Wait.CUSTOM)
                tas2 = await self.bot.api.method_accumulative("wall.getById", {}, {"posts": "-145935681_512"},
                                                              sender=sender, wait=Wait.CUSTOM)
                tas3 = await self.bot.api.method_accumulative("wall.getById", {}, {"posts": "-145935681_511"},
                                                              sender=sender, wait=Wait.CUSTOM)

                if tas1 is False and tas2 is False and tas3 is False:
                    return

                await asyncio.gather(tas1, tas2, tas3, loop=self.bot.loop, return_exceptions=True)

            self.assertEqual(tas1.result()["id"], 515)
            self.assertEqual(tas2.result()["id"], 512)
            self.assertEqual(tas3.result()["id"], 511)

        self.bot.do(work())

class TestVkUtils(unittest.TestCase):
    def check(self, message):
        self.assertLessEqual(len(message), MAX_LENGHT)
        self.assertGreaterEqual(len(message), 1)

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


if __name__ == '__main__':
    unittest.main()
