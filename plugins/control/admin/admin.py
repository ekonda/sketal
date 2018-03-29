from handler.base_plugin import CommandPlugin, DEFAULTS

from skevk import traverse, parse_user_id

import time

# TODO:
# Add `meta` to Storage
# Add saving (local->all and storage->(vip, admins, banned))

class AdminPlugin(CommandPlugin):
    __slots__ = ("commands_base", "commands_get_list", "commands_add_to_list",
        "set_admins", "commands_remove_from_list", "admins", "moders",
        "banned", "vip", "show_all")

    def __init__(self, bslist=None, cglist=None, catl=None, crfl=None, admins=None,
            banned=None, vip=None, set_admins=True, prefixes=(), strict=False,
            show_all=True):
        """Allows admins to ban people and control admins for plugins.
        Requires StoragePlugin. Admins are global. Moders are local for chats"""

        if not bslist:
            bslist = ("контроль",)

        def prepare(elms):
            return tuple(traverse(list(list(pr + " " + e for e in elms)
                for pr in bslist)))

        if not cglist:
            cglist = ("список",)

        if not catl:
            catl = ("добавить",)

        if not crfl:
            crfl = ("убрать",)

        self.commands_base = bslist
        self.commands_get_list = prepare(cglist)
        self.commands_add_to_list = prepare(catl)
        self.commands_remove_from_list = prepare(crfl)

        super().__init__(*(self.commands_base + self.commands_get_list +
            self.commands_add_to_list + self.commands_remove_from_list),
            prefixes=prefixes,strict=strict)

        self.admins = list(admins or DEFAULTS["ADMINS"])
        self.banned = list(banned or [])
        self.vip = list(vip or [])

        self.set_admins = set_admins
        self.show_all = show_all

        self.description = [
            "Администрационные команды",
            self.prefixes[-1] + self.commands_get_list[0] + " [админов, модеров, банов, випов]",
            self.prefixes[-1] + self.commands_add_to_list[0] + " [админа, модера, бан, вип] <пользователь>",
            self.prefixes[-1] + self.commands_remove_from_list[0] + " [админа, модера, бан, вип]"
        ]

    def initiate(self):
        if not self.set_admins:
            return

        for plugin in self.handler.plugins:
            if hasattr(plugin, "admins"):
                plugin.admins = self.admins

    def stop(self):
        pass # self.save()

    async def clean_user(self, msg, user_id):
        try:
            msg.meta["moders"].remove(user_id)
        except ValueError:
            pass

        try:
            self.admins.remove(user_id)
        except ValueError:
            pass

        try:
            self.banned.remove(user_id)
        except ValueError:
            pass

    async def process_message(self, msg):
        command, text = self.parse_message(msg)

        if not self.show_all and not msg.meta["is_admin_or_moder"]:
            return await msg.answer("У вас недостаточно прав.")

        if command in self.commands_base and not text:
            return await msg.answer("\n".join(self.description[1:]))

        if command in self.commands_get_list:
            if not text or text not in ("админов", "модеров", "банов", "випов"):
                return await msg.answer(self.prefixes[-1] +
                    self.commands_get_list[0] + " [админов, модеров, банов, випов]")

            if text == "админов":
                if not self.admins:
                    return await msg.answer("Никого нет!")

                return await msg.answer("Администраторы:\n👆 " + "\n👆 ".join(
                    msg.meta["chat_get_cached_name"](m) for m in self.admins))

            if text == "модеров":
                if not msg.meta["data_chat"]["moders"]:
                    return await msg.answer("Никого нет!")

                return await msg.answer("Модераторы:\n👉 " + "\n👉 ".join(
                    msg.meta["chat_get_cached_name"](m)
                        for m in msg.meta["data_chat"]["moders"]))

            if text == "банов":
                if not self.banned:
                    return await msg.answer("Никого нет!")

                return await msg.answer("Заблокированные пользователи:\n👺 " +
                    "\n👺 ".join(msg.meta["chat_get_cached_name"](m) for m in self.banned))

            if text == "випов":
                if not self.vip:
                    return await msg.answer("Никого нет!")

                return await msg.answer("Особые пользователя:\n👻 " +
                    "\n👻 ".join(msg.meta["chat_get_cached_name"](m) for m in self.vip))

        # ------------------------------------------------------------------ #

        args = text.split()

        if not args or len(args) < 2 or args[0] not in ("админа", "модера", "бан", "вип"):
            return await msg.answer(self.prefixes[-1] + command +
                " [админа, модера, бан, вип] <пользователь>")

        target_user = await parse_user_id(msg)

        if not target_user:
            return await msg.answer("👀 Целевой пользователь не найден.")

        target_user_name = target_user
        if "chat_get_cached_name" in msg.meta:
            target_user_name = msg.meta["chat_get_cached_name"](target_user)

        # ------------------------------------------------------------------ #

        if command in self.commands_add_to_list:
            if args[0] == "админа":
                if not msg.meta["is_admin"]:
                    return await msg.answer("🤜🏻 У вас недостаточно прав.")

                if target_user in self.admins:
                    return await msg.answer(f"🤜🏻 Пользователь \"{target_user_name}\" "
                        "уже администратор!")

                await self.clean_user(msg, target_user)
                self.admins.append(target_user)

                return await msg.answer(f"🙌 Пользователь \"{target_user_name}\" "
                    "теперь администратор!")

            if args[0] == "модера":
                if not msg.meta["is_admin_or_moder"]:
                    return await msg.answer("🤜🏻 У вас недостаточно прав.")

                if target_user in msg.meta["moders"]:
                    return await msg.answer(f"🤜🏻 Пользователь \"{target_user_name}\" "
                        "уже модератор!")

                if target_user in self.admins:
                    return await msg.answer(f"🤜🏻 Пользователь \"{target_user_name}\" "
                        "уже администратор!")

                await self.clean_user(msg, target_user)
                msg.meta["moders"].append(target_user)

                return await msg.answer(f"🙌 Пользователь \"{target_user_name}\" "
                    "теперь модератор!")

            if args[0] == "бан":
                if not msg.meta["is_admin_or_moder"]:
                    return await msg.answer("🤜🏻 У вас недостаточно прав.")

                if target_user in self.banned:
                    return await msg.answer(f"🤜🏻 Пользователь \"{target_user_name}\" "
                        "уже заблокирован!")

                if target_user in msg.meta["moders"] or target_user in self.admins:
                    return await msg.answer(f"🤜🏻 Пользователь \"{target_user_name}\" "
                        "не может быть заблокирован!")

                await self.clean_user(msg, target_user)
                self.banned.append(target_user)

                return await msg.answer(f"🙌 Пользователь \"{target_user_name}\" "
                    "теперь заблокирован!")

            if args[0] == "вип":
                if not msg.meta["is_admin_or_moder"]:
                    return await msg.answer("У вас недостаточно прав.")

                if target_user in self.vip:
                    return await msg.answer(f"🤜🏻 Пользователь \"{target_user_name}\" "
                        "уже VIP!")

                self.vip.append(target_user)

                return await msg.answer(f"🙌 Пользователь \"{target_user_name}\" "
                    "теперь VIP!")
        # ------------------------------------------------------------------ #

        if command in self.commands_remove_from_list:
            if args[0] == "админа":
                if not msg.meta["is_admin"]:
                    return await msg.answer("🤜🏻 У вас недостаточно прав.")

                if target_user not in self.admins:
                    return await msg.answer(f"🤜🏻 Пользователь \"{target_user_name}\" "
                        "не администратор!")

                self.admins.remove(target_user)

                return await msg.answer(f"🙌 Пользователь \"{target_user_name}\" "
                    "теперь не администратор!")

            if args[0] == "модера":
                if not msg.meta["is_admin_or_moder"]:
                    return await msg.answer("🤜🏻 У вас недостаточно прав.")

                if target_user not in msg.meta["moders"]:
                    return await msg.answer(f"🤜🏻 Пользователь \"{target_user_name}\" "
                        "не модератор!")

                msg.meta["moders"].remove(target_user)

                return await msg.answer(f"🙌 Пользователь \"{target_user_name}\" "
                    "теперь не модератор!")

            if args[0] == "бан":
                if not msg.meta["is_admin_or_moder"]:
                    return await msg.answer("🤜🏻 У вас недостаточно прав.")

                if target_user not in self.banned:
                    return await msg.answer(f"🤜🏻 Пользователь \"{target_user_name}\" "
                        "не заблокирован!")

                self.banned.remove(target_user)

                return await msg.answer(f"🙌 Пользователь \"{target_user_name}\" "
                    "теперь разблокирован!")

            if args[0] == "вип":
                if not msg.meta["is_admin_or_moder"]:
                    return await msg.answer("🤜🏻 У вас недостаточно прав.")

                if target_user not in self.vip:
                    return await msg.answer(f"🤜🏻 Пользователь \"{target_user_name}\" "
                        "не VIP!")

                self.vip.remove(target_user)

                return await msg.answer(f"🙌 Пользователь \"{target_user_name}\" "
                    "теперь не VIP!")

    async def global_before_message_checks(self, msg):
        if msg.user_id in self.banned:
            return False

        if msg.meta["data_chat"] is None:
            msg.meta["is_moder"] = False
            msg.meta["moders"] = []
        else:
            if "moders" not in msg.meta["data_chat"]:
                msg.meta["data_chat"]["moders"] = []

            msg.meta["is_moder"] = msg.user_id in msg.meta["data_chat"]["moders"]
            msg.meta["moders"] = msg.meta["data_chat"]["moders"]

        msg.meta["is_vip"] = msg.user_id in self.vip
        msg.meta["is_admin"] = msg.user_id in self.admins
        msg.meta["is_admin_or_moder"] = msg.meta["is_admin"] or msg.meta["is_moder"]

        msg.meta["vip"] = self.vip
        msg.meta["admins"] = self.admins
        msg.meta["banned"] = self.banned
