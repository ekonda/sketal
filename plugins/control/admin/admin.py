from handler.base_plugin import BasePlugin

from vk.helpers import parse_user_id


class AdminPlugin(BasePlugin):
    __slots__ = ("admins", "moders", "banset", "prefixes", "commands", "setadmins")

    def __init__(self, commands=None, admins=None, moders=None, banset=None, prefixes=(), setadmins=True):
        """Allows admins to ban people and control admins for plugins.
        Admins are global.
        Moders are local for chats"""

        super().__init__()

        self.commands = list(commands) if commands else ["ban", "unban", "admin", "unadmin", "moder", "unmoder", "banned", "admins"]
        self.admins = list(admins) if admins else list()
        self.moders =  moders if moders else {}
        self.banset = list(banset) if banset else list()
        self.setadmins = setadmins
        self.prefixes = prefixes

        self.load()

    def initiate(self):
        if not self.setadmins:
            return

        for plugin in self.handler.plugins:
            if hasattr(plugin, "admins"):
                plugin.admins = self.admins

    def get_pathes(self):
        return self.get_path("/admins.notjson"), self.get_path("/moders.notjson"), self.get_path("/batset.notjson")

    def stop(self):
        self.save()

    def load(self):
        path_admins, path_moders, path_banset = self.get_pathes()

        try:
            with open(path_admins, "r") as o:
                for u in o.read().split(","):
                    if u and int(u) not in self.admins: self.admins.append(int(u))
        except FileNotFoundError:
            pass

        try:
            with open(path_moders, "r") as o:
                current_chat = None
                for u in o.read().split(","):
                    if not u:
                        continue

                    if u[:2] == "ci":
                        current_chat = int(u[2:])
                    else:
                        moders = self.moders.get(current_chat, [])

                        if int(u) not in moders:
                            moders.append(int(u))
                            self.moders[current_chat] = moders
        except FileNotFoundError:
            pass

        try:
            with open(path_banset, "r") as o:
                for u in o.read().split(","):
                    if u and int(u) not in self.banset and int(u) not in self.admins: self.banset.append(u)
        except FileNotFoundError:
            pass

    def save(self):
        path_admins, path_moders, path_banset = self.get_pathes()

        with open(path_admins, "w") as o:
            for u in self.admins:
                o.write(str(u) + ",")

        with open(path_moders, "w") as o:
            for k, v in self.moders.items():
                o.write("ci" + str(k) + ",")

                for u in v:
                    o.write(str(u) + ",")

        with open(path_banset, "w") as o:
            for u in self.banset:
                o.write(str(u) + ",")

    async def check_message(self, msg):
        return any(c in msg.text for c in self.commands)

    async def process_message(self, msg):
        text = msg.text

        for p in self.prefixes:
            if msg.text.startswith(p):
                text = text.replace(p, "", 1)
                break

        else:
            return

        if text == self.commands[6]:
            users = ""

            temp = ""
            temp_amount = 0

            for bu in self.banset:
                temp += bu + ","
                temp_amount += 1

                if temp_amount > 99:
                    for u in (await self.api.users.get(user_ids=temp) or []):
                        users += u["first_name"] + " " + u["last_name"] + f" ({u['id']}), "

                    temp = ""
                    temp_amount = 0

            if temp_amount:
                for u in (await self.api.users.get(user_ids=temp) or []):
                    users += u["first_name"] + " " + u["last_name"] + f" ({u['id']}), "

            return await msg.answer("Заблокированные пользователи:\n" + (users[:-2] if users[:-2] else "Нет"))

        if text == self.commands[7]:
            a_users = ""
            for u in (await self.api.users.get(user_ids=",".join(str(u) for u in self.admins)) or []):
                a_users += u["first_name"] + " " + u["last_name"] + f" ({u['id']}), "

            m_users = ""
            for u in (await self.api.users.get(user_ids=",".join(str(u) for u in msg.meta["moders"])) or []):
                m_users += u["first_name"] + " " + u["last_name"] + f" ({u['id']}), "

            return await msg.answer("Администраторы:\n" + (a_users[:-2] if a_users[:-2] else "Нет") + "\n"
                                    "Модераторы:\n" + (m_users[:-2] if m_users[:-2] else "Нет"))

        if not msg.meta["is_admin"] and not msg.meta["is_moder"]:
            return await msg.answer("Вы не администратор!")

        puid = await parse_user_id(msg)

        if not puid:
            return await msg.answer(f"Ошибка при определении id пользователя!")

        if text.startswith(self.commands[0]):
            if puid in self.banset:
                return await msg.answer("Уже забанен!")

            if puid in self.admins or puid in msg.meta["moders"]:
                return await msg.answer("Нельзя забанить администратора!")

            self.banset.append(puid)
            return await msg.answer(f"Успешно забанен: {puid}!")

        if text.startswith(self.commands[1]):
            if puid not in self.banset:
                return await msg.answer(f"Пользователь не забанен: {puid}!")
            else:
                self.banset.remove(puid)
                return await msg.answer(f"Пользователь разбанен: {puid}!")

        if text.startswith(self.commands[2]):
            if not msg.meta["is_admin"]:
                return await msg.answer(f"Вы не администратор!")

            if len(self.admins) > 99:
                return await msg.answer(f"Уже максимум администраторов!")

            if puid in self.admins:
                return await msg.answer("Уже администратор!")

            if puid in self.banset:
                return await msg.answer("Этот пользователь забанен!")

            self.admins.append(puid)
            return await msg.answer(f"Успешно сделан администратором: {puid}!")

        if text.startswith(self.commands[3]):
            if puid not in self.admins:
                return await msg.answer(f"Пользователь не администратор: {puid}!")
            else:
                self.admins.remove(puid)
                return await msg.answer(f"Пользователь разжалован из администраторов: {puid}!")

        if text.startswith(self.commands[4]):
            if len(msg.meta["moders"]) > 50:
                return await msg.answer(f"Уже максимум модераторов!")

            if puid in msg.meta["moders"]:
                return await msg.answer("Уже модератор!")

            msg.meta["moders"].append(puid)
            return await msg.answer(f"Успешно сделан модератором: {puid}!")

        if text.startswith(self.commands[5]):
            if puid not in msg.meta["moders"]:
                return await msg.answer(f"Пользователь не модератор: {puid}!")
            else:
                msg.meta["moders"].remove(puid)
                return await msg.answer(f"Пользователь разжалован из модераторов: {puid}!")

    async def global_before_message(self, msg, plugin):
        for n, s in (("admin", self.admins), ("banned", self.banset)):
            msg.meta[f"is_{n}"] = msg.user_id in s

        moders = self.moders.get(msg.chat_id, [])
        msg.meta[f"is_moder"] = msg.user_id in moders
        self.moders[msg.chat_id] = moders

        msg.meta["admins"] = self.admins
        msg.meta["moders"] = self.moders[msg.chat_id]
        msg.meta["banset"] = self.banset

        return not msg.meta["is_banned"]
