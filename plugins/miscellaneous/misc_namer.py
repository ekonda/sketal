from handler.base_plugin import CommandPlugin
from utils import Message

class NamerPlugin(CommandPlugin):
    __slots__ = ("old_answer",)

    def __init__(self, *commands, prefixes=None, strict=False):
        """Answers with information about bot. Requires: StoragePlugin."""

        if not commands:
            commands= ("зови меня",)

        super().__init__(*commands, prefixes=prefixes, strict=strict)

        self.description = [f"\"Зови меня\"",
                            f"Указывает, как бот будет обращаться к вам.",
                            f"{self.command_example()} [имя] - установить себе псевдоним.",
                            f"{self.command_example()} никак - удалить свой псевдоним."]

        _answer = Message.answer
        async def new_answer(self, message="", **kwargs):
            if self.meta["data_user"] and "nickname" in self.meta["data_user"]:
                message = self.meta["data_user"]["nickname"] + ",\n" + message

            return await _answer(self, message, **kwargs)
        Message.answer = new_answer

    async def process_message(self, msg):
        if not msg.meta["data_user"]:
            return await msg.answer("👊 Нет нужного плагина для этого \_:c_/")

        _, name = self.parse_message(msg, full=True)

        fname = name.strip().lower()

        if len(fname) > 64:
            return await msg.answer("👊 Слишком длинное имя!")

        if any(mat in fname for mat in ("член", "гей", "хуй", "пидор")):
            return await msg.answer("👊 Нет.")

        if not fname or fname == "никак":
            if "nickname" in msg.meta["data_user"]:
                del msg.meta["data_user"]["nickname"]
        else:
            msg.meta["data_user"]["nickname"] = name

        return await msg.answer("💭 Хорошо")
