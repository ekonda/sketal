from handler.base_plugin import BasePlugin

import peewee
import datetime, random
from decimal import *

# Requirements:
# PeeweePlugin
#

class AzinoPlugin(BasePlugin):
    __slots__ = ("prefixes", "commands", "manager", "player", "player_log",
                 "tiles", "current", "pwmanager", "min_bet", "admins", "bonus")

    def __init__(self, *commands, min_bet=5, bonus=250, prefixes=("",), admins=()):
        """Slot machines with coins"""

        self.prefixes = prefixes

        self.commands = commands if commands else ("azino", "az")
        self.admins = admins
        self.pwmanager = None

        self.min_bet = Decimal(str(min_bet))
        self.bonus = Decimal(str(bonus))

        self.player = None
        self.player_log = None

        self.current = set()

        # tile = (weight, reward)
        self.tiles = {"🍑": (3, 1.25), "🍇": (3, 1.5), "🍓": (3, 2), "🍒": (2, 2.5), "7⃣": (1, 10)}

        for k, v in self.tiles.items():
            self.tiles[k] = Decimal(str(v[0])), Decimal(str(v[1]))

        super().__init__()

        self.description = ["Казино \"🔥 AZINO777 🔥\"",
                            f"{self.prefixes[0]}{self.commands[0]} - показать помощь."]

    def initiate(self):
        if self.pwmanager is None:
            raise ValueError("Please, use PeeweePlugin with set_manager=True for this plugin to work or set pwmanager for plugin yourself.")

        class AzinoPlayer(peewee.Model):
            user_id = peewee.BigIntegerField(primary_key=True, unique=True)
            balance = peewee.DecimalField(max_digits=20, decimal_places=2, default=Decimal("250"))
            collected = peewee.DateTimeField(default=datetime.datetime.now() - datetime.timedelta(days=1))

            class Meta:
                database = self.pwmanager.database

        class AzinoPlayerLog(peewee.Model):
            user_id = peewee.BigIntegerField()
            comment = peewee.TextField(default="")
            delta = peewee.DecimalField(max_digits=20, decimal_places=2)

            created = peewee.DateTimeField(default=datetime.datetime.now)

            class Meta:
                database = self.pwmanager.database

        with self.pwmanager.allow_sync():
            AzinoPlayer.create_table(True)
            AzinoPlayerLog.create_table(True)

        self.player = AzinoPlayer
        self.player_log = AzinoPlayerLog

    async def check_message(self, msg):
        text = ""
        for p in self.prefixes:
            if msg.text.startswith(p):
                text = msg.text[len(p):].strip()
                break
        else:
            return False

        for command in self.commands:
            if text.startswith(command):
                msg.meta["__azino_subcommand"] = text[len(command):].strip()
                return True

        return False

    def get_tile(self, add=None):
        if add is None:
            add = {}

        total = sum(float(w) for w, _ in self.tiles.values())
        total += sum(float(w) for w in add.values())

        r = Decimal(str(random.uniform(0, total)))

        upto = 0
        for k, v in self.tiles.items():
            upto += v[0] + add.get(k, 0)
            if upto >= r: return k, v[1]

        assert False, "Getting tile failed"

    async def process_message(self, msg):
        cmd = msg.meta["__azino_subcommand"]
        try:
            cmd_num = float(cmd)
        except ValueError:
            cmd_num = False

        if msg.user_id in self.current:
            return
        self.current.add(msg.user_id)

        p, c = await self.pwmanager.get_or_create(self.player, user_id=msg.user_id)

        if cmd_num is not False:
            bet = Decimal(str(round(cmd_num, 2)))

            if bet < self.min_bet:
                self.current.remove(msg.user_id)
                return await msg.answer(f"Минимальная ставка: {round(self.min_bet, 2)}!")

            if p.balance - bet < 0:
                self.current.remove(msg.user_id)
                return await msg.answer(f"У вас не хватает средств! Ваш баланс: {round(p.balance, 2)}")

            text = "🔥 AZINO777 🔥\n"
            resu = []
            add = {}
            for i in range(3):
                resu.append(self.get_tile(add))
                add[resu[-1][0]] = add.get(resu[-1][0], 0) + 9 - 5 * i

            if resu[0][0] == resu[1][0] == resu[2][0]:
                p.balance += bet * resu[1][1] - bet
                text += f"🌝 Вы выиграли: {bet * resu[1][1]} (x{resu[2][1]})\n"

                await self.pwmanager.create(self.player_log, user_id=msg.user_id, delta=bet * resu[1][1] - bet, comment=f"Stavka ({round(bet, 2)})")
            else:
                p.balance -= bet
                text += f"🌚 Вы потеряли: {round(bet, 2)}\n"

                await self.pwmanager.create(self.player_log, user_id=msg.user_id, delta=-bet, comment=f"Stavka ({round(bet, 2)})")

            text += f"\n🎲 Ваша комбинация: {resu[0][0]}{resu[1][0]}{resu[2][0]}\n" \
                    f"✨ Ваш баланс: {round(p.balance, 2)}"

            if msg.user_id not in self.current:
                return await msg.answer("Ошибка. Вы ты аргрвыафы...")

            self.current.remove(msg.user_id)
            await self.pwmanager.update(p)

            return await msg.answer(text)

        if cmd.lower() in ("баланс", "ба"):
            self.current.remove(msg.user_id)

            return await msg.answer(f"✨ Ваш баланс: {round(p.balance)}")

        if cmd.lower() in ("бонус",):
            if datetime.datetime.now() - p.collected < datetime.timedelta(days=1):
                self.current.remove(msg.user_id)
                return await msg.answer("Вы уже собрали свой бонус сегодня! Приходите завтра!")

            p.balance += self.bonus
            p.collected = datetime.datetime.now()
            await self.pwmanager.update(p)

            self.current.remove(msg.user_id)

            return await msg.answer(f"✨ Бонус получен: {self.bonus}! \n✨ Новый баланс: {round(p.balance, 2)}")


        if cmd.lower() in ("история", ):
            logs = self.player_log
            logs = await self.pwmanager.execute(logs.select().where(logs.user_id == msg.user_id).order_by(logs.created.desc()).limit(10))

            text = ""
            for log in logs:
                 text += f"> {log.comment} {log.delta} ({log.created})\n"

            if not text:
                text = "Ничего нет!"
            else:
                text = "История:\n" + text

            self.current.remove(msg.user_id)

            return await msg.answer(text)

        admin = msg.user_id in self.admins

        if admin and (cmd.lower().startswith("добавить ") or cmd.lower().startswith("отнять ")):
            try:
                c, i, a = cmd.lower().split(" ")
                i = int(i)
            except ValueError:
                self.current.remove(msg.user_id)

                return await msg.answer("💬 добавить [user_id] [amount] - добавить пользователю user_id amount\n"
                                        "💬 отнять [user_id] [amount] - отнять у пользователя user_id amount ")
            except Exception:
                import traceback
                traceback.print_exc()

                self.current.remove(msg.user_id)
                return await msg.answer("Произошла ошибка.")

            p, _ = await self.pwmanager.get_or_create(self.player, user_id=i)
            delta = Decimal(Decimal("1" if c == "добавить" else "-1") * Decimal(a))
            p.balance += delta

            await self.pwmanager.update(p)
            self.current.remove(msg.user_id)

            await self.pwmanager.create(self.player_log, user_id=msg.user_id, delta=delta, comment="Adminova volya")

            return await msg.answer(f"✨ Новый баланс: {p.balance}")

        self.current.remove(msg.user_id)
        return await msg.answer("🔥 AZINO777 🔥\n"
                                "💬 [ставка] - сыграть на ставку\n"
                                "💬 баланс - проверить баланс\n"
                                "💬 бонус - получить ежедневный бонус")
                                # ADMIN:
                                # 💬 добавить [user_id] [amount] - добавить пользователю user_id amount
                                # 💬 отнять [user_id] [amount] - отнять у пользователя user_id amount
