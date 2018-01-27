from handler.base_plugin_command import CommandPlugin

import peewee

import asyncio, uuid, time, re


class RememberPlugin(CommandPlugin):
    __slots__ = ("after_pa", "after_re", "remember_list", "help", "pwmanager",
                 "add_entity", "sub_entity", "clear_peer", "iterate_entities",
                 "get_size_of_list", "place_data", "use_db")

    def __init__(self, *commands, prefixes=None, strict=False, use_db=False):
        """Creates notification poping up after specified time"""

        super().__init__(*commands, prefixes=prefixes, strict=strict)

        self.remember_list = []  # (uniq_id, peer_id, firetime, text, atta, user_id)
        self.pwmanager = None
        self.use_db = use_db

        self.add_entity = None
        self.sub_entity = None
        self.clear_peer = None
        self.place_data = None
        self.get_size_of_list = None
        self.iterate_entities = None

        self.after_pa = r"^ ?(через )?(\d+(\.\d+)?) (секунд.?|минут.?|час.{0,2}|день|дня|дней)? ?"
        self.after_re = re.compile(self.after_pa)

        self.description = [f"Напоминания",
                            f"{self.command_example()} отменить [id напоминания] - отменить напоминание с указанным id. Отменяет все, если 0.",
                            f"{self.command_example()} через [единица времени] [мера времени] [текст]- напомнить [текст] через указанное время.\n"
                            f"Мера времени: секунды, минуты, часы, дни. Меру можно не указывать. По умолчанию - секунды"]

        self.help = "\n".join(self.description)

    def initiate(self):
        if not self.use_db or self.pwmanager is None:
            async def add_entity(ne):
                for i, e in enumerate(self.remember_list):
                    if ne[2] > e[2]:
                        self.remember_list.insert(i, ne)
                        return

                self.remember_list.append(ne)

            self.add_entity = add_entity

            async def sub_entity(e_id):
                for i, e in enumerate(self.remember_list):
                    if str(e_id) == str(e[0]):
                        self.remember_list.pop(i)
                        return True

                return False

            self.sub_entity = sub_entity

            async def clear_peer(peer_id):
                self.remember_list = list(e for e in self.remember_list if e[1] != peer_id)

            self.clear_peer = clear_peer

            self.place_data = lambda e: e

            async def get_size_of_list():
                return len(self.remember_list)

            self.get_size_of_list = get_size_of_list

            async def iterate_entities():
                return list(e for e in self.remember_list if e[2] <= time.time())

            self.iterate_entities = iterate_entities

        else:
            class Entity(peewee.Model):
                firetime = peewee.TimestampField()

                user_id = peewee.BigIntegerField()
                peer_id = peewee.BigIntegerField()
                uniq_id = peewee.CharField(primary_key=True, unique=True, max_length=64)

                text = peewee.TextField()
                atta = peewee.TextField()

                class Meta:
                    database = self.pwmanager.database

            with self.pwmanager.allow_sync():
                Entity.create_table(True)

            async def add_entity(ne):
                await self.pwmanager.get_or_create(Entity, firetime=ne[2], uniq_id=ne[0], peer_id=ne[1], text=ne[3], atta=ne[4], user_id=ne[5])

            self.add_entity = add_entity

            async def sub_entity(e_id):
                return await self.pwmanager.execute(Entity.delete().where(Entity.uniq_id == e_id)) > 0

            self.sub_entity = sub_entity

            async def clear_peer(peer_id):
                return await self.pwmanager.execute(Entity.delete().where(Entity.peer_id == peer_id)) > 0

            self.clear_peer = clear_peer

            self.place_data = lambda e: (e.uniq_id, e.peer_id, e.firetime, e.text, e.atta, e.user_id)

            async def get_size_of_list():
                return await self.pwmanager.count(Entity.select()) > 0

            self.get_size_of_list = get_size_of_list

            async def iterate_entities():
                return await self.pwmanager.execute(Entity.select().where(Entity.firetime <= time.time()))

            self.iterate_entities = iterate_entities

        asyncio.ensure_future(self.sender())

    async def sender(self):
        while True:
            for e in await self.iterate_entities():
                unid, peer_id, _, message, attachment, user_id = self.place_data(e)
                await self.api.messages.send(peer_id=peer_id, message=f"[id{user_id}|✉] > " + message, attachment=attachment)
                await self.sub_entity(unid)

            await asyncio.sleep(1)

    async def process_message(self, msg):
        command, text = self.parse_message(msg)

        if text.startswith("отменить"):
            v = text.split(" ")[-1]

            if v.strip() == "отменить":
                return await msg.answer("Вы не указали цель отмены!\n" + self.help)

            if v == "0":
                await self.clear_peer(peer_id)
                return await msg.answer("✂ Все напоминания удалены!")

            if await self.sub_entity(v):
                return await msg.answer("✂ Напоминание удалено!")
            else:
                return await msg.answer("✂ Напоминание не существует!")

        wait_time = None

        match = self.after_re.search(text)

        if not match:
            return await msg.answer(self.help)

        full_text = msg.full_text[-(len(text) - len(match.group(0))):]
        short_text = full_text if len(full_text) < 16 else full_text[:14] + "..."
        value = float(match.group(2))
        step = match.group(4) or ""

        if step.startswith("секунд"):
            step = 1
        elif step.startswith("минут"):
            step = 60
        elif step.startswith("час"):
            step = 3600
        elif step in ("день", "дня", "дней"):
            step = 86400
        else:
            step = 1

        wait_time = value * step

        uid = uuid.uuid4()

        await self.add_entity((uid, msg.peer_id, time.time() + wait_time, full_text, ",".join(str(a) for a in await msg.get_full_attaches()), msg.user_id))

        if msg.peer_id != msg.user_id:
            await msg.answer("💬 Напоминание успешно добавлено!")

        await self.api.messages.send(message=f"🎫 Уникальный идентификатор напоминания \"{short_text}\": {uid}", user_id=msg.user_id)
