from handler.base_plugin_command import CommandPlugin
from vk.utils import Wait
from vk.helpers import upload_photo

import asyncio
import aiohttp
import io


class DispatchPlugin(CommandPlugin):
    __slots__ = ("admins", )

    def __init__(self, *commands, prefixes=None, strict=False, admins=()):
        """Allows admins to send out messages to users."""

        super().__init__(*commands, prefixes=prefixes, strict=strict)

        self.admins = admins

    async def process_message(self, msg):
        if msg.user_id not in self.admins and not msg.meta.get("is_moder"):
            return await msg.answer("Вы не администратор.")

        cmd_len = len(msg.meta.get("__prefix", "")) + len(msg.meta.get("__command", ""))

        message = msg.full_text[cmd_len:].strip()
        attachment = ""

        for a in await msg.get_full_attaches():
            if a.type != "photo":
                attachment += str(a) + ","

            if a.type == "photo" and a.url:
                async with aiohttp.ClientSession() as sess:
                    async with sess.get(a.url) as resp:
                        new_a = await upload_photo(self.api, io.BytesIO(await resp.read()))

                        if not new_a:
                            continue

                        attachment += str(new_a) + ","

        await msg.answer("Приступаю к рассылке!")

        if await self.dispatch(message, attachment) is False:
            return await msg.answer("Ошибка при отправлении! Попробуйте позже!")

        return await msg.answer("Рассылка закончена!")

    async def dispatch(self, message, attachment):
        dialogs = await self.bot.api.messages.getDialogs(count=1, preview_length=1)

        if not dialogs or "count" not in dialogs:
            return False

        dialogs = dialogs["count"]
        users = set()

        tasks = []

        with self.bot.api.mass_request():
            for i in range(int(dialogs / 200) + 1):
                tasks.append(await self.bot.api(wait=Wait.CUSTOM).messages.getDialogs(count=200, preview_length=1))

            future = asyncio.gather(*tasks, return_exceptions=True)

        await asyncio.wait_for(future, None)

        for r in future.result():
            if not r:
                continue

            for dialog in r.get("items", []):
                if "message" not in dialog or "user_id" not in dialog["message"]:
                    continue

                users.add(int(dialog["message"]["user_id"]))

        for i, u in enumerate(users):
            await self.bot.api(wait=Wait.NO).messages.send(user_id=u, message=message, attachment=attachment)

            if i % 25 == 0:
                await asyncio.sleep(0.2)
