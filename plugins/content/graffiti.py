from handler.base_plugin_command import CommandPlugin
from vk.helpers import upload_graffiti

import aiohttp, io


class GraffitiPlugin(CommandPlugin):
    __slots__ = ()

    def __init__(self, *commands, prefixes=None, strict=False):
        if not commands:
            commands = "граффити",

        super().__init__(*commands, prefixes=prefixes, strict=strict)

        self.description = ["Граффити.", f"{self.prefixes[-1]}{self.commands[0]} - превращает прикреплённый документ или изображение в граффити."]

    async def process_message(self, msg):
        fgra = None

        if msg.brief_attaches:
            for a in await msg.get_full_attaches():
                if a.type == "photo" or a.type == "doc":
                    fgra = a

        if not fgra or not fgra.url:
            return await msg.answer("Пришлите файл для превращения!")

        async with aiohttp.ClientSession() as sess:
            async with sess.get(fgra.url) as resp:
                at = await upload_graffiti(self.api, io.BytesIO(await resp.read()), "gra." + (fgra.ext if fgra.ext else "png"))

        if not at:
            return await msg.answer("Не удалось создать граффити!")

        return await msg.answer("Ваш документ: " + str(at), attachment=at)
