from handler.base_plugin import BasePlugin
from vk.helpers import parse_user_id

import peewee_async, peewee, asyncio, random, time

# Requirements:
# PeeweePlugin
#

class DuelerPlugin(BasePlugin):
    __slots__ = ("commands", "prefixes", "models", "pwmanager", "active")

    def __init__(self, prefixes=("",), _help="помощь", me="я", pay="зп", duel="вызов", top="топ",
                 accept="принять", auct="аукцион", bet="ставка", add="добавить", remove="удалить", postprefix="дуэли"):
        """Nice game "Dueler"."""

        super().__init__()

        self.commands = [(postprefix + " " if postprefix else "") + c.lower() for c in (me, _help, pay, duel, accept, auct, bet, add, remove, top)]  # [-1] == [9]
        self.prefixes = prefixes

        self.pwmanager = None
        self.models = []
        self.active = True

        self.description = ["Игра \"Dueler\"",
                            f"{self.prefixes[0]}{self.commands[1]} - показать помощь по игре."]

    def initiate(self):
        if self.pwmanager is None:
            raise ValueError("Please, use PeeweePlugin with set_manager=True for this plugin to work or set pwmanager for plugin yourself.")

        class Equipment(peewee.Model):
            name = peewee.TextField()
            slot = peewee.TextField()
            power = peewee.IntegerField()

            class Meta:
                database = self.pwmanager.database
                indexes = (
                    (('name', 'power', 'slot'), True),
                )

        class Player(peewee.Model):
            user_id = peewee.BigIntegerField()
            chat_id = peewee.BigIntegerField()

            last_payout = peewee.BigIntegerField(default=0)

            lastmsg = peewee.BigIntegerField(default=0)
            lastreq = peewee.BigIntegerField(default=0)

            state = peewee.IntegerField(default=0)
            money = peewee.IntegerField(default=0)

            wins = peewee.IntegerField(default=0)
            losses = peewee.IntegerField(default=0)

            helm = peewee.ForeignKeyField(Equipment, on_delete='SET NULL', null=True, related_name="hemled")
            chest = peewee.ForeignKeyField(Equipment, on_delete='SET NULL', null=True, related_name="chested")
            weapon = peewee.ForeignKeyField(Equipment, on_delete='SET NULL', null=True, related_name="weaponed")\

            class Meta:
                database = self.pwmanager.database
                indexes = (
                    (('user_id', 'chat_id'), True),
                )

        class Auct(peewee.Model):
            chat_id = peewee.BigIntegerField()

            lot1 = peewee.ForeignKeyField(Equipment, on_delete='SET NULL', null=True, related_name="lot1ed")
            lot2 = peewee.ForeignKeyField(Equipment, on_delete='SET NULL', null=True, related_name="lot2ed")
            lot3 = peewee.ForeignKeyField(Equipment, on_delete='SET NULL', null=True, related_name="lot3ed")
            lot4 = peewee.ForeignKeyField(Equipment, on_delete='SET NULL', null=True, related_name="lot4ed")
            lot5 = peewee.ForeignKeyField(Equipment, on_delete='SET NULL', null=True, related_name="lot5ed")

            bet1 = peewee.IntegerField(default=0)
            bet2 = peewee.IntegerField(default=0)
            bet3 = peewee.IntegerField(default=0)
            bet4 = peewee.IntegerField(default=0)
            bet5 = peewee.IntegerField(default=0)

            buyer1 = peewee.BigIntegerField(default=0)
            buyer2 = peewee.BigIntegerField(default=0)
            buyer3 = peewee.BigIntegerField(default=0)
            buyer4 = peewee.BigIntegerField(default=0)
            buyer5 = peewee.BigIntegerField(default=0)

            endt = peewee.BigIntegerField(default=0)

            class Meta:
                database = self.pwmanager.database
                indexes = (
                    (('chat_id', ), True),
                )

        class Duel(peewee.Model):
            userid1 = peewee.BigIntegerField()
            userid2 = peewee.BigIntegerField()
            chat_id = peewee.BigIntegerField()

            class Meta:
                database = self.pwmanager.database
                indexes = (
                    (('chat_id', 'userid1', 'userid2'), True),
                )

        with self.pwmanager.allow_sync():
            Equipment.create_table(True)
            Player.create_table(True)
            Duel.create_table(True)
            Auct.create_table(True)

        self.models = Auct, Duel, Player, Equipment

    @staticmethod
    def get_level(score):
        e = 0

        for i in range(100):
            score -= e * 1.2 + 50

            if score <= 0:
                return i, -score

        return 100, -1

    async def global_before_message_checks(self, msg):
        msg.meta["__cplayer"] = await self.get_or_create_player(msg.chat_id, msg.user_id)

        if time.time() - msg.meta["__cplayer"].lastmsg < 15:
            return

        if msg.meta["__cplayer"].lastmsg == 0 or time.time() - msg.meta["__cplayer"].lastmsg < 60 * 5:
            msg.meta["__cplayer"].state = min(100, msg.meta["__cplayer"].state + 2)

        elif time.time() - msg.meta["__cplayer"].lastmsg < 60 * 10:
            msg.meta["__cplayer"].state = min(100, msg.meta["__cplayer"].state + 1)

        elif time.time() - msg.meta["__cplayer"].lastmsg < 60 * 20:
            msg.meta["__cplayer"].state = max(0, msg.meta["__cplayer"].state - 10)

        elif time.time() - msg.meta["__cplayer"].lastmsg >= 60 * 20:
            msg.meta["__cplayer"].state = max(0, msg.meta["__cplayer"].state - 50)

        msg.meta["__cplayer"].lastmsg = time.time()

    async def check_message(self, msg):
        prefix = None
        pltext = ""

        for p in self.prefixes:
            if msg.full_text.startswith(p):
                prefix = p
                pltext = msg.full_text.replace(p, "", 1)
                break

        if prefix is None:
            return False

        for c in self.commands:
            if pltext.startswith(c + " ") or pltext.startswith(c + "\n") or pltext == c:
                break
        else:
            return False

        msg.meta["__prefix"] = prefix
        msg.meta["__pltext"] = pltext

        return True

    async def get_or_create_player(self, chat_id, user_id):
        Auct, Duel, Player, Equipment = self.models

        try:
            equipments = (
                Equipment
                .select()
            )
            players = (
                Player
                .select()
                .where(
                    (Player.chat_id == chat_id) &
                    (Player.user_id == user_id)
                )
            )

            player = list(await self.pwmanager.prefetch(players, equipments))[0]
        except IndexError:
            player = await peewee_async.create_object(Player, chat_id=chat_id, user_id=user_id)

        return player

    async def get_or_create_auct(self, chat_id):
        Auct, Duel, Player, Equipment = self.models

        try:
            equipments = (
                Equipment
                .select()
            )
            aucts = (
                Auct
                .select()
                .where(
                    Auct.chat_id == chat_id
                )
            )

            auct = list(await self.pwmanager.prefetch(aucts, equipments))[0]
        except IndexError:
            auct = await peewee_async.create_object(Auct, chat_id=chat_id)

        return auct

    async def process_message(self, msg):
        if msg.meta["__pltext"].lower() == self.commands[1]:
            me, _help, pay, duel, accept, auct, bet, add, remove, top = self.commands
            p = self.prefixes[0]

            return await msg.answer(f'''У каждoго учаcтникa чата есть свой игровой пeрсoнаж, имеющий:
- Оcновная xapaктеpиcтика - cилу 💪, золото 💰 и cнaряжeниe (шлeм ⛑, брoня 🛡, оружиe ⚔), котopoe увеличивает силу персoнaжа и пoкупается нa aукциoнe. Такжe у пepсонажа eсть состояние (в %) - онo определяетcя отноcитeльно текущeгo актива учacтника в чaтe.
- Аукциoн мoжно пpoвoдить не чащe, чeм pаз в чaс, и каждый paз нa нeм выcтавляются cлучайнoе снapяжeние со cлучайными xарактериcтикaми (чeм выше xapактеpистики, тeм pеже выпaдaeт).
- Рaз в час вcем пеpсoнажам чaта можнo выдавать жалованиe - oбщая сумма для чaтa завиcит oт кoличеcтвa активныx в пocлeднee врeмя учаcтников, a количество жaлoвaния на кaждoгo пepcонaжа - в завиcимocти oт поcледнего актива учaстников относитeльно oбщего (у жaловaния нет нaкoплений, eсли нe выдавaть жалoвание - оно cгoрaет)
- Пeрсoнaжи могут вызывaть друг дpуга нa дуэли (кaждый пepcонаж мoжет вызвaть проводить дуэль рaз в час)
На дуэли cpавниваeтся oбщая cилa учаcтникoв, кoтoрая являeтcя cуммoй:
1) вcего cнaряжeния учacтникa
2) состояния
3) удaчи, каждый рaз oпpеделяется случaйным oбpaзoм, но не бoльше 15% oт oбщeй силы
У того, у кoго итоговая сила бoльше, больше вероятностей победить!

Команды:
{p}{me} - информация о персонаже.
{p}{pay} - собрать вознаграждение.
{p}{duel} -вызвать на дуэль.
{p}{accept} -принять вызов.
{p}{auct} - начать аукцион.
{p}{top} - показать лучших бойцов.
{p}{_help} - помощь''')

        Auct, Duel, Player, Equipment = self.models

        player = msg.meta["__cplayer"] or await self.get_or_create_player(msg.chat_id, msg.user_id)

        if msg.meta["__pltext"].lower().startswith(self.commands[9]):
            top = await self.pwmanager.execute(Player.select().where(Player.chat_id == msg.chat_id).order_by(Player.wins.desc()).limit(10))

            text = "👑 Самые мощные игроки:\n"

            users = {}
            if "__chat_data" in msg.meta:
                for u in msg.meta["__chat_data"].users:
                    users[u["id"]] = u["first_name"] + " " + u["last_name"]

            for i, player in enumerate(top):
                text += (
                    str(i + 1) + ". 😎 " + users.get(player.user_id, f"Пользователь \"{player.user_id}\"") +
                    "\nПобед: " + str(player.wins)  + " // Поражений: " + str(player.losses)  + "\n"
                )

            return await msg.answer(text)

        if msg.meta["__pltext"].lower().startswith(self.commands[8]):
            if not msg.meta.get("is_admin") and not msg.meta.get("is_moder"):
                return msg.answer("Недостаточно прав.")

            try:
                name = " ".join(msg.meta["__pltext"][len(self.commands[8]):].strip().split(" "))

                if not name:
                    raise ValueError()
            except (ValueError, KeyError, IndexError):
                return await msg.answer("Как надо: " + self.prefixes[0] + self.commands[8] + " [название предмета]")


            await self.pwmanager.execute(Equipment.delete().where(Equipment.name == name))

            return await msg.answer("Готово!")

        if msg.meta["__pltext"].lower().startswith(self.commands[7]):
            if not msg.meta.get("is_admin") and not msg.meta.get("is_moder"):
                return await msg.answer("Недостаточно прав.")

            try:
                power, slot, *names = msg.meta["__pltext"][len(self.commands[7]):].strip().split(" ")

                name = " ".join(names)

                if not name:
                    raise ValueError()
            except (ValueError, KeyError, IndexError):
                return await msg.answer("Как надо: " + self.prefixes[0] + self.commands[7] + " [сила] [слот (helm, weapon или chest)] [название предмета]")

            if slot not in ("helm", "weapon", "chest"):
                return await msg.answer("Доступные слоты для экипировки: helm, weapon, chest")

            for i in range(5):
                tpower = round((0.75 + random.random() * 0.5) * round(float(power)))

                try:
                    await peewee_async.create_object(Equipment, name=name, slot=slot, power=tpower)
                except peewee.IntegrityError:
                    pass

            return await msg.answer("Готово!")

        if msg.meta["__pltext"].lower().startswith(self.commands[6]):
            auct = await self.get_or_create_auct(msg.chat_id)

            if time.time() - auct.endt >= 0:
                return await msg.answer("Аукцион закончен")

            try:
                _, lot, bet = msg.meta["__pltext"][len(self.commands[6]):].split(" ")
                bet = int(bet)
            except (KeyError, ValueError):
                return await msg.answer("Как надо ставить: " + self.prefixes[0] + self.commands[6] + " [номер лота] [ставка]")

            olot = getattr(auct, f"lot{lot}")
            obet = getattr(auct, f"bet{lot}")
            obuyer = getattr(auct, f"buyer{lot}")

            if obet >= bet:
                return await msg.answer("Ставка должна быть больше текущей!")

            if player.money < bet:
                return await msg.answer("У вас недостаточно средств для ставки!")

            if obuyer != 0:
                prbuyer = await self.get_or_create_player(msg.chat_id, obuyer)
                prbuyer.money += obet
                await self.pwmanager.update(prbuyer)

            player.money -= bet

            setattr(auct, f"bet{lot}", bet)
            setattr(auct, f"buyer{lot}", player.user_id)

            await self.pwmanager.update(auct)
            await self.pwmanager.update(player)

            text = "💰 Аукцион:\n"

            for i in range(1, 6):
                olot = getattr(auct, f"lot{i}")
                obet = getattr(auct, f"bet{i}")

                text += (
                    f"{i}. " + ("⛑" if olot.slot == "helm" else ("🛡" if olot.slot == "chest" else "⚔")) +
                    " " + olot.name + " (💪 " + str(olot.power) + ") - " + str(obet) + "$\n"
                )

            text += "\nАукцион закончится через 5 минут. Вещи получат игроки, поставившие наибольшую ставку на предмет. "\
                    "Предметы заменят текущие. Проигравшим вернут деньги.\n\nСтавка: " + self.prefixes[0] + self.commands[6] + " [номер лота] [ставка]"

            return await msg.answer(text)

        if msg.meta["__pltext"].lower() == self.commands[5]:
            auct = await self.get_or_create_auct(msg.chat_id)

            if time.time() - auct.endt < 60 * 66:
                return await msg.answer(f"💰 Вы сможете начать аукцион через {66 - round((time.time() - auct.endt) / 60)} мин.")

            equipments = list(await self.pwmanager.execute(Equipment.select()))

            if len(equipments) == 0:
                return await msg.answer("Недостаточно экипировки.")

            if len(equipments) < 5:
                equipments = [equipments[0]] * 5

            random.shuffle(equipments)

            text = "💰 Аукцион:\n"

            for i in range(5):
                setattr(auct, f"lot{i + 1}", equipments[i])
                setattr(auct, f"buyer{i + 1}", 0)

                bet = 0
                for _ in range(max(1, equipments[i].power - 3)):
                    bet += 20 + round(random.random() * 10)

                setattr(auct, f"bet{i + 1}", bet)

                text += (
                    f"{i + 1}. " + ("⛑" if equipments[i].slot == "helm" else ("🛡" if equipments[i].slot == "chest" else "⚔")) +
                    " " + equipments[i].name + " (" + str(equipments[i].power) + ") - " + str(bet) + "$\n"
                )

            auct.endt = time.time() + 60 * 5

            await self.pwmanager.update(player)
            await self.pwmanager.update(auct)

            text += "\nАукцион закончится через 5 минут. Вещи получат игроки, поставившие наибольшую ставку на предмет. "\
            "Предметы заменят текущие. Проигравшим вернут деньги.\n\nСтавка: " + self.prefixes[0] + self.commands[6] + " [номер лота] [ставка]"

            async def finish_auct(chat_id):
                await asyncio.sleep(60 * 5)

                auct = await self.get_or_create_auct(msg.chat_id)

                for i in range(1, 6):
                    olot = getattr(auct, f"lot{i}")
                    obuyer = getattr(auct, f"buyer{i}")

                    if obuyer == 0:
                        continue

                    p = await self.get_or_create_player(chat_id=chat_id, user_id=obuyer)

                    if olot.slot == "helm":
                        p.helm = olot
                    elif olot.slot == "chest":
                        p.chest = olot
                    else:
                        p.weapon = olot

                    await self.pwmanager.update(p)

                return await msg.answer("Аукцион закончен.")

            asyncio.ensure_future(finish_auct(chat_id=msg.chat_id))

            return await msg.answer(text)

        if msg.meta["__pltext"].lower() == self.commands[4]:
            try:
                duel = await self.pwmanager.get(Duel, chat_id=msg.chat_id, userid2=msg.user_id)
            except Duel.DoesNotExist:
                return await msg.answer("Никто не вызывал вас на дуэль!")

            player1 = await self.get_or_create_player(msg.chat_id, duel.userid1)
            player2 = player

            await peewee_async.delete_object(duel)

            level1, _ = self.get_level(player1.wins * 10 + player1.losses * 5)
            level2, _ = self.get_level(player2.wins * 10 + player2.losses * 5)

            epower1 = 9
            if player1.helm:
                epower1 += player1.helm.power
            if player1.chest:
                epower1 += player1.chest.power
            if player1.weapon:
                epower1 += player1.weapon.power
            apower1 = epower1 + round(epower1 * (player1.state / 100), 2)
            lpower1 = apower1 + round(apower1 * level1 / 100, 2)
            power1 = lpower1 + round(lpower1 * 0.15 * random.random(), 2)

            epower2 = 9
            if player2.helm:
                epower2 += player2.helm.power
            if player2.chest:
                epower2 += player2.chest.power
            if player2.weapon:
                epower2 += player2.weapon.power
            apower2 = epower2 + round(epower2 * (player2.state / 100), 2)
            lpower2 = apower2 + round(apower2 * level2 / 100, 2)
            power2 = lpower2 + round(lpower2 * 0.15 * random.random(), 2)

            player1win = random.random() * (power1 + power2) < power1

            users = await self.api.users.get(user_ids=f"{duel.userid1},{duel.userid2}")
            if len(users) == 1:
                users.append(users[0])

            text = (
                "Битва персонажей 🤺\"" + users[0]["first_name"] + " " + users[0]["last_name"]  + "\" и "
                "🤺\"" + users[1]["first_name"] + " " + users[1]["last_name"]  + "\"\n"
                "💪 Уровни: " + str(level1) + " / " + str(level2) + "\n"
                "💪 Cостояния: " + str(player1.state) + "% / " + str(player2.state) + "%\n"
                "💪 Экипировка: " + str(epower1) + " / " + str(epower2) + "\n"
                "💪 Актив сила: " + str(round(apower1 - epower1, 2))  + " / " + str(round(apower2 - epower2, 2)) + "\n"
                "💪 Сила опыта: " + str(round(lpower1 - apower1, 2))  + " / " + str(round(lpower2 - apower2, 2)) + "\n\n"
                "💪 Сила удачи: " + str(round(power1 - lpower1, 2))  + " / " + str(round(power2 - lpower2, 2)) + "\n\n"
                "💪 СИЛА: " + str(round(power1, 2))  + " / " + str(round(power2, 2)) + "\n\n"
            )

            if player1win:
                text += (
                    "После долгой схватки, " + users[0]["first_name"] + " " + users[0]["last_name"] +
                    " и " + (player1.weapon.name.lower() if player1.weapon else "ничего") + " пробили "
                    + (player2.chest.name.lower() if player2.chest else "грудь") + " своего оппонента."
                )

                player1.wins += 1
                player1.money += 5
                player2.losses += 1
            else:
                text += (
                    "После долгой схватки, " + users[1]["first_name"] + " " + users[1]["last_name"] +
                    " и " + (player2.weapon.name.lower() if player2.weapon else "ничего") + " пробили "
                    + (player1.chest.name.lower() if player1.chest else "грудь") + " своего оппонента."
                )

                player2.wins += 1
                player2.money += 5
                player1.losses += 1

            text += "\n\nПобедитель: " + (users[0]["first_name"] + " " + users[0]["last_name"] if player1win
                                          else users[1]["first_name"] + " " + users[1]["last_name"]) + " (награда - 5$)"

            await self.pwmanager.update(player1)
            await self.pwmanager.update(player2)

            return await msg.answer(text)

        if msg.meta["__pltext"].lower().startswith(self.commands[3]):
            if time.time() - player.lastreq < 60 * 3:
                 return await msg.answer(f"Вы можете бросать не более 1 вызова в 3 минуты. Осталось: {60 * 3 - round(time.time() - player.lastreq)} сек.")

            target_id = await parse_user_id(msg)

            if not target_id or target_id < 0:
                return await msg.answer("Укажите вашу цель или перешлите её сообщение.")

            if msg.user_id == target_id:
                return await msg.answer("Вы не можете вызвать на дуэль себя.")

            try:
                await peewee_async.create_object(Duel, chat_id=msg.chat_id, userid1=msg.user_id, userid2=target_id)
            except peewee.IntegrityError:
                return await msg.answer(f"[id{target_id}|Вы готовы принять вызов?]\nНапишите \"{self.prefixes[0]}{self.commands[4]}\", чтобы принять.")

            player.lastreq = time.time()

            await self.pwmanager.update(player)

            return await msg.answer(f"[id{target_id}|Вы готовы принять вызов?]\nНапишите \"{self.prefixes[0]}{self.commands[4]}\", чтобы принять.")

        if msg.meta["__pltext"].lower() == self.commands[2]:
            if time.time() - player.last_payout >= 60 * 60:
                gain = 50 + round((player.state / 100) * 200)

                player.last_payout = time.time()
                player.money += gain
                await self.pwmanager.update(player)

                return await msg.answer(f"💰 Вы заработали: {gain}$\n💰 Заходите через час!")

            await self.pwmanager.update(player)

            return await msg.answer(f"💰 Вы сможете получить свою зп через {60 - round((time.time() - player.last_payout) / 60)} мин.")


        elif msg.meta["__pltext"].lower() == self.commands[0]:
            users =await self.api.users.get(user_ids=msg.user_id)
            user = users[0]

            level, exp_left = self.get_level(player.wins * 10 + player.losses * 5)

            text = (
                "💬 Информация о персонаже:\n"
                f"🌳 {user['first_name']} {user['last_name']}\n"
                f"🌳 Уровень: {level}\n"
                f"🌳 Опыта до повышения уровня: {round(exp_left)}\n"
                f"🌳 Состояние: {player.state}%\n"
                f"🌳 Богатства: {player.money}$\n"
                f"🌳 Победы/поражения: {player.wins}/{player.losses}\n"
                "🌳 Снаряжение:\n"
            )

            if player.helm:
                text += "- ⛑ " + player.helm.name + " (💪 " + str(player.helm.power) + ")"
            else:
                text += "- ⛑ Ничего"

            text += "\n"

            if player.chest:
                text += "- 🛡 " + player.chest.name + " (💪 " + str(player.chest.power) + ")"
            else:
                text += "- 🛡 Ничего"

            text += "\n"

            if player.weapon:
                text += "- ⚔ " + player.weapon.name + " (💪 " + str(player.weapon.power) + ")"
            else:
                text += "- ⚔ Ничего"

            await self.pwmanager.update(player)

            return await msg.answer(text)
