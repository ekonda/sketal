from handler.base_plugin_command import CommandPlugin
from utils import traverse

import uuid, defusedxml.ElementTree as ET
import aiohttp

SUPPORTED = {
    "ogg": "audio/ogg;codecs=opus",
    "spx": "audio/x-speex",
    "webm": "audio/webm;codecs=opus",
}

CHUNK_SIZE = 1024 ** 2

class Audio2TextPlugin(CommandPlugin):
    __slots__ = ("key", "active", "active_once", "commands_once",
        "commands_turn_on", "commands_turn_off", "configurations")

    def __init__(self, commands_once=None, commands_turn_on=None,
            commands_turn_off=None, key=None, prefixes=None, strict=False):
        if not key:
            raise AttributeError("No api key specified! Get it here: https://tech.yandex.ru/speechkit/cloud/")

        if not commands_once:
            commands_once = ("что сказал", "что сказал?", "что сказала?", "что сказала",)

        if not commands_turn_on:
            commands_turn_on = ("в текст", "в текст on",)

        if not commands_turn_off:
            commands_turn_off = ("не надо в текст", "в текст off", "в текст оф",)

        super().__init__(*(commands_once + commands_turn_on + commands_turn_off),
            prefixes=prefixes, strict=strict)

        self.key = key

        self.commands_once = commands_once
        self.commands_turn_on = commands_turn_on
        self.commands_turn_off = commands_turn_off

        self.active = False
        self.active_once = False
        self.configurations = {}  # 0 - off, 1 - on, 2 - once

    async def check_message(self, msg):
        hm = await super().check_message(msg)

        if not hm and self.configurations.get(msg.peer_id, 0) > 0:
            msg.meta["__command"] = ""
            msg.meta["__arguments"] = ""
            msg.meta["__arguments_full"] = ""
            return True

        return hm

    async def process_message(self, msg):
        command, text = self.parse_message(msg)

        if command in self.commands_turn_on:
            if self.configurations.get(msg.peer_id, 0) in (0, 2):
                self.configurations[msg.peer_id] = 1
                return await msg.answer("Буду всё слушать и записывать :D")

            return await msg.answer("Я и так всё слушаю и записываю \_C:_/")

        if command in self.commands_turn_off:
            del self.configurations[msg.peer_id]
            return await msg.answer("Как хочешь...")

        sound, exten = None, None

        async def check(ats):
            if not ats:
                return None, None

            for at in ats:
                if at.type == "doc" and at.ext in SUPPORTED:
                    async with aiohttp.ClientSession() as sess:
                        async with sess.get(at.url) as resp:
                            return await resp.read(), at.ext

            return None, None

        if msg.brief_attaches:
            sound, exten = await check(await msg.get_full_attaches())

        if sound is None and msg.brief_forwarded:
            for m in traverse(await msg.get_full_forwarded()):
                 sound, exten = await check(await m.get_full_attaches())

                 if sound is not None:
                     break

        if sound is None and command in self.commands_once:
            if self.configurations.get(msg.peer_id, 0) in (0, 2):
                self.configurations[msg.peer_id] = 2
                return await msg.answer("Переведу следующее в текст ;)")

            return await msg.answer("Я и так всё перевожу \_C:_/")

        if sound is None:
            if msg.is_out or self.configurations.get(msg.peer_id, 0) == 1:
                return False

            return await msg.answer("Мне нечего перевести в текст :(")

        @aiohttp.streamer
        def sound_sender(writer):
            chunki = 0
            chunk = sound[chunki * CHUNK_SIZE: (chunki + 1) * CHUNK_SIZE]

            while chunk:
                yield from writer.write(chunk)

                chunki += 1
                chunk = sound[chunki * CHUNK_SIZE: (chunki + 1) * CHUNK_SIZE]

        url = 'http://asr.yandex.net/asr_xml' + \
            '?uuid=%s&key=%s&topic=%s&lang=%s' % (uuid.uuid4().hex, \
                self.key, 'notes', 'ru-RU')

        async with aiohttp.ClientSession() as sess:
            async with sess.post(url, data=sound_sender(),
                    headers={"Content-Type": SUPPORTED[exten]}) as resp:
                response = await resp.text()

                if resp.status != 200:
                    return await msg.answer("Мне не получилось ничего разобрать или я больше не работаю!")

        root = ET.fromstring(response)

        if root.attrib['success'] not in ("1", 1):
            return await msg.answer("Мда. Нет.")

        return await msg.answer("\"" + str(root[0].text) + "\"")
