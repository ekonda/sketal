from handler.base_plugin_command import CommandPlugin
from vk.utils import EventType

import peewee, aiohttp, json, io


class LockChatPlugin(CommandPlugin):
    __slots__ = ("pwmanager", "flags", "ChatLock")

    def __init__(self, *commands, prefixes=None, strict=False, picture_flag="пикчу", title_flag="название", invite_flag="состав"):
        """Plugin allowing admins or moders to lock chat's state"""

        if not commands:
            commands = "lock",

        super().__init__(*commands, prefixes=prefixes, strict=strict)

        self.flags = [picture_flag, title_flag, invite_flag]

        self.pwmanager = None
        self.ChatLock = None

        self.description = ["Оборона беседы",
                            f"{self.prefixes[-1]}{self.commands[0]} [флаги через пробелы] - установить настройки защиты беседы. Если флаг присутствует, "
                            "то изменение соответствующего атрибута запрещено.",
                            f"Флаги: {picture_flag} (обложка не будет меняться), {title_flag} (название не будет меняться), "
                            "{invite_flag} (нельзя покидать или вступать в беседу)",
                            "Отсутствие флага разрешает изменение атрибута."]

    def initiate(self):
        if self.pwmanager is None:
            raise ValueError("Please, use PeeweePlugin with set_manager=True for this plugin to work or set pwmanager for plugin yourself.")

        class ChatLock(peewee.Model):
            chat_id = peewee.BigIntegerField()

            old_pic = peewee.TextField(null=True)
            hold_pi = peewee.BooleanField(default=False)
            hold_ti = peewee.BooleanField(default=False)
            hold_en = peewee.BooleanField(default=False)

            class Meta:
                database = self.pwmanager.database
                indexes = (
                    (('chat_id', ), True),
                )

        with self.pwmanager.allow_sync():
            ChatLock.create_table(True)

        self.ChatLock = ChatLock

    async def check_event(self, evnt):
        return evnt.type == EventType.ChatChange

    async def process_event(self, evnt):
        if evnt.user_id == self.api.get_current_id():
            return False

        lock, _ = await self.pwmanager.get_or_create(self.ChatLock, chat_id=evnt.chat_id)

        if evnt.source_act == "chat_invite_user":
            if lock.hold_en:
                return await self.api.messages.removeChatUser(chat_id=evnt.chat_id, user_id=evnt.source_mid)

        elif evnt.source_act == "chat_kick_user":
            if lock.hold_en:
                return await self.api.messages.addChatUser(chat_id=evnt.chat_id, user_id=evnt.source_mid)

        elif evnt.source_act == "chat_title_update":
            if lock.hold_ti:
                return await self.api.messages.editChat(chat_id=evnt.chat_id, title=evnt.old_title)

        elif evnt.source_act == "chat_photo_update" or evnt.source_act == "chat_photo_remove":
            if lock.hold_pi:
                sender = self.api.get_default_sender("photos.getChatUploadServer")

                resp = await self.api(sender).photos.getChatUploadServer(chat_id=evnt.chat_id)
                if not resp or not resp.get("upload_url"): return
                upload_url = resp["upload_url"]

                data = aiohttp.FormData()
                async with aiohttp.ClientSession() as sess:
                    async with sess.get(lock.old_pic) as resp:
                        data.add_field('file', io.BytesIO(await resp.read()), filename="picture.jpg", content_type='multipart/form-data')

                    async with sess.post(upload_url, data=data) as resp:
                        result = json.loads(await resp.text())

                if not result or not result.get("response"): return

                return await self.api(sender).messages.setChatPhoto(file=result["response"])

        return False

    async def process_message(self, msg):
        if msg.chat_id == 0:
            return

        if "is_admin" in msg.meta and not msg.meta["is_admin"] and "is_moder" in msg.meta and not msg.meta["is_moder"]:
            return await msg.answer("Вы не имеете доступа к этой команде.")

        lock, _ = await self.pwmanager.get_or_create(self.ChatLock, chat_id=msg.chat_id)

        flags = self.parse_message(msg)[1].lower().split()
        pi, ti, en = False, False, False

        for uf in flags:
            took = False

            for i, f in enumerate(self.flags):
                if not f.startswith(uf):
                    continue

                if took:
                    return await msg.answer(f"Флаг не удалось опознать: \"{uf}\".")
                took = True

                if i == 0:
                    pi = True
                elif i == 1:
                    ti = True
                elif i == 2:
                    en = True

            if not took:
                return await msg.answer(f"Флаг не удалось опознать: \"{uf}\".")

        if pi:
            chat = await self.api.messages.getChat(chat_id=msg.chat_id)

            if not chat:
                return await msg.answer("Произошла ошибка. Попробуйте позже.")

            lock.old_pic = chat.get("photo_200")
            lock.hold_pi = True
        else:
            lock.hold_pi = False

        lock.hold_ti = ti
        lock.hold_en = en

        await self.pwmanager.update(lock)

        willbesaved = ", ".join(i for i in
            (
                "обложка беседы" if pi else "",
                "название беседы" if ti else "",
                "состав беседы" if en else ""
            ) if i
        )

        return await msg.answer (
            "Будет сохранено: " + (willbesaved if willbesaved else "ничего")
        )
