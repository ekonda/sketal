from handler.base_plugin import CommandPlugin, DEFAULTS

from skevk import parse_user_id


class AdminPlugin(CommandPlugin):
    __slots__ = ("commands_get_list", "commands_add_to_list",
        "commands_remove_from_list", "admins", "moders", "banned", "set_admins")

    def __init__(self, cglist=None, catl=None, crfl=None, admins=None,
            moders=None, banned=None, set_admins=True, prefixes=(), strict=False):
        """Allows admins to ban people and control admins for plugins.
        Admins are global. Moders are local for chats"""

        if not cglist:
            self.commands_get_list = cglist= ("контроль список",)

        if not catl:
            self.commands_add_to_list = catl = ("контроль добавить",)

        if not crfl:
            self.commands_remove_from_list = crfl = ("контроль убрать",)

        super().__init__(*(cglist + cglist + crfl), prefixes=prefixes, strict=strict)

        self.admins = admins or DEFAULTS["ADMINS"]
        self.moders =  moders or []
        self.banned = banned or []

        self.set_admins = set_admins

    def initiate(self):
        if not self.set_admins:
            return

        for plugin in self.handler.plugins:
            if hasattr(plugin, "admins"):
                plugin.admins = self.admins

    def stop(self):
        pass # self.save()

    async def process_message(self, msg):
        command, text = self.parse_message(msg)

        if command in self.commands_get_list:
            if not text or text not in ("админы", "модеры", "блок"):
                return await msg.answer(self.prefixes[0] +
                    self.commands_get_list[0] + " [админы, модеры, блок]")

            if text == "админы":
                pass

    async def _global_before_message(self, msg, plugin):
        for n, s in (("admin", self.admins), ("banned", self.banset)):
            msg.meta[f"is_{n}"] = msg.user_id in s

        moders = self.moders.get(msg.chat_id, [])
        msg.meta[f"is_moder"] = msg.user_id in moders
        self.moders[msg.chat_id] = moders

        msg.meta["admins"] = self.admins
        msg.meta["moders"] = self.moders[msg.chat_id]
        msg.meta["banset"] = self.banset

        return not msg.meta["is_banned"]
