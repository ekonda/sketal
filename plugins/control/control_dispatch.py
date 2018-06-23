from handler.base_plugin import CommandPlugin
from utils import upload_photo

import asyncio, aiohttp, io


class DispatchPlugin(CommandPlugin):
    def __init__(self, *commands, prefixes=None, strict=False):
        """Allows admins to send out messages to users."""

        if not commands:
            commands = ("разослать",)

        super().__init__(*commands, prefixes=prefixes, strict=strict)

    async def process_message(self, msg):
        if not msg.meta["is_admin_or_moder"]:
            return await msg.answer("🤜🏻 У вас недостаточно прав.")

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

        await msg.answer("> Приступаю к рассылке!")

        if await self.dispatch(message, attachment) is False:
            return await msg.answer("< Ошибка при отправлении! Попробуйте позже!")

        return await msg.answer("< Рассылка закончена!")

    async def dispatch(self, message, attachment):
        dialogs = await self.bot.api.messages.getDialogs(count=1, preview_length=1)

        if not dialogs or "count" not in dialogs:
            return False

        dialogs = dialogs["count"]
        users = set()

        tasks = []

        for i in range(int(dialogs / 200) + 1):
            tasks.append(await self.bot.api(wait="custom").messages.getDialogs(count=200, preview_length=1))

        await asyncio.wait_for(
            asyncio.gather(*tasks, return_exceptions=True), None)

        for r in tasks:
            if not r or not r.result():
                continue

            r = r.result()

            for dialog in r.get("items", []):
                if "message" not in dialog or "user_id" not in dialog["message"]:
                    continue

                users.add(int(dialog["message"]["user_id"]))

        for i, u in enumerate(users):
            await self.bot.api(wait="no").messages.send(user_id=u, message=message, attachment=attachment)

            if i % 25 == 0:
                await asyncio.sleep(0.2)
