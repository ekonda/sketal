from handler.base_plugin import CommandPlugin, DEFAULTS

from utils import traverse, parse_user_id, parse_user_name


class StaffControlPlugin(CommandPlugin):
    __slots__ = ("commands_base", "commands_get_list", "commands_add_to_list",
        "set_admins", "commands_remove_from_list", "admins", "moders",
        "banned", "vip", "show_all")

    def __init__(self, bslist=None, cglist=None, catl=None, crfl=None, admins=None,
            set_admins=True, prefixes=(), strict=False, show_all=True):
        """Allows admins to ban people and control admins for plugins.
        Requires StoragePlugin. Admins are global. Moders are local for chats."""

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

        self.order = (-89, 89)

        self.admins = list(admins or DEFAULTS["ADMINS"])

        self.set_admins = set_admins
        self.show_all = show_all

        self.description = [
            "Администрационные команды",
            self.prefixes[-1] + self.commands_get_list[0] + " [админов, модеров, банов, випов] - показать список.",
            self.prefixes[-1] + self.commands_add_to_list[0] + " [админа, модера, бан, вип] <пользователь> - добавить в список.",
            self.prefixes[-1] + self.commands_remove_from_list[0] + " [админа, модера, бан, вип] - убрать из списка."
        ]

    def initiate(self):
        if not self.set_admins:
            return

        for plugin in self.handler.plugins:
            if hasattr(plugin, "admins"):
                plugin.admins = self.admins

    async def process_message(self, msg):
        command, text = self.parse_message(msg)

        if not self.show_all and not msg.meta["is_admin_or_moder"]:
            return await msg.answer("🤜🏻 У вас недостаточно прав.")

        if command in self.commands_base and not text:
            return await msg.answer(self.description[0] + "\n🤝 " +
                "\n🤝 ".join(self.description[1:]))

        admin_lists = msg.meta["data_meta"].getraw("admin_lists")
        if msg.meta["data_chat"]:
            moders = msg.meta["data_chat"].getraw("moders")
        else:
            moders = []

        if command in self.commands_get_list:
            if not text or text not in ("админов", "модеров", "банов", "випов"):
                return await msg.answer(self.prefixes[-1] +
                    self.commands_get_list[0] + " [админов, модеров, банов, випов]")

            if text == "админов":
                if not admin_lists["admins"]:
                    return await msg.answer("Никого нет!")

                usrs = []

                for m in admin_lists["admins"]:
                    usrs.append(await parse_user_name(m, msg) + f" vk.com/id{m}")

                return await msg.answer("Администраторы:\n👆 " + "\n👆 ".join(usrs))

            if text == "модеров":
                if not moders:
                    return await msg.answer("Никого нет!")

                usrs = []

                for m in moders:
                    usrs.append(await parse_user_name(m, msg) + f" vk.com/id{m}")

                return await msg.answer("Модераторы:\n👉 " + "\n👉 ".join(usrs))

            if text == "банов":
                if not admin_lists["banned"]:
                    return await msg.answer("Никого нет!")

                usrs = []

                for m in admin_lists["banned"]:
                    usrs.append(await parse_user_name(m, msg) + f" vk.com/id{m}")

                return await msg.answer("Заблокированные пользователи:\n👺 " +
                    "\n👺 ".join(usrs))

            if text == "випов":
                if not admin_lists["vips"]:
                    return await msg.answer("Никого нет!")

                usrs = []

                for m in admin_lists["vips"]:
                    usrs.append(await parse_user_name(m, msg) + f" vk.com/id{m}")

                return await msg.answer("Особые пользователя:\n👻 " +
                    "\n👻 ".join(usrs))

        # ------------------------------------------------------------------ #

        args = text.split()

        if not args or len(args) < 2 or args[0] not in ("админа", "модера", "бан", "вип"):
            return await msg.answer(self.prefixes[-1] + command +
                " [админа, модера, бан, вип] <пользователь>")

        target_user = await parse_user_id(msg)

        if not target_user:
            return await msg.answer("👀 Целевой пользователь не найден.")

        target_user_name = await parse_user_name(target_user, msg)

        msg.meta["data_meta"].changed = True
        if msg.meta["data_chat"]:
            msg.meta["data_chat"].changed = True

        # ------------------------------------------------------------------ #

        if command in self.commands_add_to_list:
            if args[0] == "админа":
                if not msg.meta["is_admin"]:
                    return await msg.answer("🤜🏻 У вас недостаточно прав.")

                if target_user in admin_lists["admins"]:
                    return await msg.answer(f"🤜🏻 Пользователь \"{target_user_name}\" "
                        "уже администратор!")

                if target_user in admin_lists["banned"]:
                    return await msg.answer(f"🤜🏻 Пользователь \"{target_user_name}\" "
                        "заблокирован!")

                admin_lists["admins"].append(target_user)

                return await msg.answer(f"🙌 Пользователь \"{target_user_name}\" "
                    "теперь администратор!")

            if args[0] == "модера":
                if not msg.meta["is_admin_or_moder"]:
                    return await msg.answer("🤜🏻 У вас недостаточно прав.")

                if target_user in moders:
                    return await msg.answer(f"🤜🏻 Пользователь \"{target_user_name}\" "
                        "уже модератор!")

                if target_user in admin_lists["admins"]:
                    return await msg.answer(f"🤜🏻 Пользователь \"{target_user_name}\" "
                        "уже администратор!")

                if target_user in admin_lists["banned"]:
                    return await msg.answer(f"🤜🏻 Пользователь \"{target_user_name}\" "
                        "заблокирован!")

                moders.append(target_user)

                return await msg.answer(f"🙌 Пользователь \"{target_user_name}\" "
                    "теперь модератор!")

            if args[0] == "бан":
                if not msg.meta["is_admin_or_moder"]:
                    return await msg.answer("🤜🏻 У вас недостаточно прав.")

                if target_user in admin_lists["banned"]:
                    return await msg.answer(f"🤜🏻 Пользователь \"{target_user_name}\" "
                        "уже заблокирован!")

                if target_user in msg.meta["moders"] or target_user in admin_lists["admins"]:
                    return await msg.answer(f"🤜🏻 Пользователь \"{target_user_name}\" "
                        "не может быть заблокирован!")

                admin_lists["banned"].append(target_user)

                return await msg.answer(f"🙌 Пользователь \"{target_user_name}\" "
                    "теперь заблокирован!")

            if args[0] == "вип":
                if not msg.meta["is_admin_or_moder"]:
                    return await msg.answer("🤜🏻 У вас недостаточно прав.")

                if target_user in admin_lists["vips"]:
                    return await msg.answer(f"🤜🏻 Пользователь \"{target_user_name}\" "
                        "уже VIP!")

                admin_lists["vips"].append(target_user)

                return await msg.answer(f"🙌 Пользователь \"{target_user_name}\" "
                    "теперь VIP!")

        # ------------------------------------------------------------------ #

        if command in self.commands_remove_from_list:
            if args[0] == "админа":
                if not msg.meta["is_admin"]:
                    return await msg.answer("🤜🏻 У вас недостаточно прав.")

                if target_user not in admin_lists["admins"]:
                    return await msg.answer(f"🤜🏻 Пользователь \"{target_user_name}\" "
                        "не администратор!")

                admin_lists["admins"].remove(target_user)

                return await msg.answer(f"🙌 Пользователь \"{target_user_name}\" "
                    "теперь не администратор!")

            if args[0] == "модера":
                if not msg.meta["is_admin"] and not target_user == self.user_id:
                    return await msg.answer("🤜🏻 У вас недостаточно прав.")

                if target_user not in moders:
                    return await msg.answer(f"🤜🏻 Пользователь \"{target_user_name}\" "
                        "не модератор!")

                moders.remove(target_user)

                return await msg.answer(f"🙌 Пользователь \"{target_user_name}\" "
                    "теперь не модератор!")

            if args[0] == "бан":
                if not msg.meta["is_admin_or_moder"]:
                    return await msg.answer("🤜🏻 У вас недостаточно прав.")

                if target_user not in admin_lists["banned"]:
                    return await msg.answer(f"🤜🏻 Пользователь \"{target_user_name}\" "
                        "не заблокирован!")

                admin_lists["banned"].remove(target_user)

                return await msg.answer(f"🙌 Пользователь \"{target_user_name}\" "
                    "теперь разблокирован!")

            if args[0] == "вип":
                if not msg.meta["is_admin_or_moder"]:
                    return await msg.answer("🤜🏻 У вас недостаточно прав.")

                if target_user not in admin_lists["vips"]:
                    return await msg.answer(f"🤜🏻 Пользователь \"{target_user_name}\" "
                        "не VIP!")

                admin_lists["vips"].remove(target_user)

                return await msg.answer(f"🙌 Пользователь \"{target_user_name}\" "
                    "теперь не VIP!")

    async def global_before_message_checks(self, msg):
        admin_lists = msg.meta["data_meta"].getraw("admin_lists")

        if admin_lists is None:
            admin_lists = msg.meta["data_meta"]["admin_lists"] = \
                {"banned": [], "admins": list(self.admins), "vips": []}

        if msg.user_id in admin_lists["banned"]:
            return False

        if msg.meta.get("data_chat") is None:
            msg.meta["is_moder"] = False
            msg.meta["moders"] = []
        else:
            if "moders" not in msg.meta["data_chat"]:
                msg.meta["data_chat"]["moders"] = []

            moders = msg.meta["data_chat"].getraw("moders")

            msg.meta["is_moder"] = msg.user_id in moders
            msg.meta["moders"] = tuple(moders)

        msg.meta["is_vip"] = msg.user_id in admin_lists["vips"]
        msg.meta["is_admin"] = msg.user_id in admin_lists["admins"]
        msg.meta["is_admin_or_moder"] = msg.meta["is_admin"] or msg.meta["is_moder"]

        msg.meta["vips"] = tuple(admin_lists["vips"])
        msg.meta["admins"] = tuple(admin_lists["admins"])
        msg.meta["banned"] = tuple(admin_lists["banned"])

        msg.meta["get_editable_admins_lists"] = \
            (lambda: msg.meta["data_meta"]["admin_lists"])
