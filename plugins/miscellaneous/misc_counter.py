from handler.base_plugin import CommandPlugin


class CounterPlugin(CommandPlugin):
    __slots__ = ()

    def __init__(self, *commands, prefixes=None, strict=False):
        """Useless plugin for counting up. Requires: StoragePlugin."""

        if not commands:
            commands = ("оп+",)

        super().__init__(*commands, prefixes=prefixes, strict=strict)

    async def process_message(self, msg):
        msg.meta["data_meta"]["123"] = "Привет"

        if "value" in msg.meta["data_user"]:
            msg.meta["data_user"]["value"] += 1
        else:
            msg.meta["data_user"]["value"] = 1

        answer = "Пользователь: " + str(msg.meta["data_user"]["value"])

        if msg.is_multichat:
            if "value" in msg.meta["data_chat"]:
                msg.meta["data_chat"]["value"] += 1
            else:
                msg.meta["data_chat"]["value"] = 1

            answer += "\nБеседа: " + str(msg.meta["data_chat"]["value"])

        return await msg.answer(answer)
