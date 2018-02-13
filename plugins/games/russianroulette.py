from handler.base_plugin import BasePlugin
import peewee_async, peewee, random, time

# Requirements:
#
# ChatMetaPlugin


class RussianRoulettePlugin(BasePlugin):
    __slots__ = ("pwmanager", "roulette", "prefixes", "start_commands", "join_commands", "shoot_commands")

    def __init__(self, start_commands=None, join_commands=None, shoot_commands=None, prefixes=()):
        """Answers with a message it received."""

        super().__init__()

        self.roulette = None
        self.pwmanager = None

        self.prefixes = prefixes
        self.start_commands = start_commands or ["бах"]
        self.shoot_commands = shoot_commands or ["🔫", "🔪", "пух"]
        self.join_commands = join_commands or ["+"]

        self.description = ["💀 Русская рулетка 💀", f"{self.prefixes[0]}{self.start_commands[0]} - начать партию."]

    def initiate(self):
        if self.pwmanager is None:
            raise ValueError("Please, use PeeweePlugin with set_manager=True for this plugin to work or set pwmanager for plugin yourself.")

        class Roulette(peewee.Model):
            chat_id = peewee.BigIntegerField(primary_key=True, unique=True)
            members = peewee.TextField(default="")
            status = peewee.IntegerField(default=-1)
            turn = peewee.IntegerField(default=0)

            start = peewee.BigIntegerField(default=0)

            class Meta:
                database = self.pwmanager.database

        with self.pwmanager.allow_sync():
            Roulette.create_table(True)

        self.roulette = Roulette

    async def check_message(self, msg):
        current_text = msg.text
        has_prefix = False
        for pref in self.prefixes:
            if current_text.startswith(pref):
                current_text = current_text.replace(pref, "", 1)
                has_prefix = True
                break

        if current_text in self.join_commands:
            msg.meta["__cmd"] = "join"

        elif current_text in self.shoot_commands:
            msg.meta["__cmd"] = "shoot"

        elif current_text in self.start_commands and has_prefix:
            msg.meta["__cmd"] = "start"

        return "__cmd" in msg.meta

    def parse_user(self, msg, user_id):
        users = {}
        if "__chat_data" in msg.meta:
            for u in msg.meta["__chat_data"].users:
                users[u["id"]] = u["first_name"] + " " + u["last_name"]

        return users.get(user_id, f"Пользователь \"{user_id}\"")

    async def process_message(self, msg):
        if not msg.chat_id:
            return await msg.answer("Только в чате можно ;)")

        roulette, c = await self.pwmanager.get_or_create(self.roulette, chat_id=msg.chat_id)

        members = roulette.members.split("a")[:-1]

        if msg.meta["__cmd"] == "start":
            if roulette.status != -1 and time.time() - roulette.start < 60 * 2.5:
                return await msg.answer("Игра уже идёт.")

            roulette.status = 0
            roulette.members = ""
            roulette.turn = 0
            roulette.start = time.time()
            await self.pwmanager.update(roulette)

            return await msg.answer(f"💀 Начинаем собирать людей на игру. Кто осмелится?\n💀 Присоединиться: {self.join_commands[0]}\n💀  Игра начнётся, когда найдётся 2 участника. Через 2.5 минуты игру можно будет оборвать, начав новую.")

        if roulette.status == -1:
            return await msg.answer("Никто сейчас не играет.")

        if msg.meta["__cmd"] == "join":
            if roulette.status == 1:
                return await msg.answer("Игра уже идёт.")

            if f"{msg.user_id}a" not in roulette.members:
                if await self.pwmanager.execute(self.roulette.update(members=self.roulette.members.concat(f"{msg.user_id}a")).where(self.roulette.chat_id == roulette.chat_id)):
                    if len(members) + 1 > 1:
                        await self.pwmanager.execute(self.roulette.update(status=1).where(self.roulette.chat_id == roulette.chat_id))
                        return await msg.answer(
                            "💀  Игра начинается.\n💀  Первым стреляет " + self.parse_user(msg, int(members[roulette.turn % len(members)])) + "\n"
                            f"💀 Выстрелить: {self.shoot_commands[0]}"
                        )
                    return await msg.answer("💀  Вы в игре.")

                return await msg.answer("💀  Что-то странно... Ошибка.")

            return await msg.answer("💀  Вы уже играете.")

        if msg.meta["__cmd"] == "shoot":
            if roulette.status == 0:
                return await msg.answer("💀 Игра ещё не началась.")

            if str(msg.user_id) != members[roulette.turn % len(members)]:
                return await msg.answer("💀 Сейчас не ваш ход.")

            if random.random() * 6 < 1 + roulette.turn / 2:
                roulette.status = -1
                await self.pwmanager.update(roulette)

                return await msg.answer("💀 Ты мёртв. Конец игры. 💀")

            roulette.turn += 1
            await self.pwmanager.update(roulette)

            return await msg.answer(
                "🙉 Ничего. Игра продолжается.\n💀 Стреляет " + self.parse_user(msg, int(members[roulette.turn % len(members)])) + "\n"
                f"💀 Выстрелить: {self.shoot_commands[0]}"
            )
