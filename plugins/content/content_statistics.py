from handler.base_plugin import CommandPlugin
from utils import parse_user_name

import time


class StatisticsPlugin(CommandPlugin):
    __slots__ = ()

    def __init__(self, *commands, prefixes=None, strict=False):
        """Stores amount of messages for users in chats. Requires: StoragePlugin."""

        if not commands:
            commands = ("статистика",)

        super().__init__(*commands, prefixes=prefixes, strict=strict)

    async def global_before_message_checks(self, msg):
        data = msg.meta["data_chat"]

        if not data:
            return

        if "chat_statistics" not in data:
            data["chat_statistics"] = {"users": {}}

        statistics = data["chat_statistics"]

        user_key = str(msg.user_id)

        if user_key not in statistics["users"]:
            statistics["users"][user_key] = {"messages": 0, "symbols": 0,
                "last_message": time.time()}

        user = statistics["users"][user_key]

        user["messages"] += 1
        user["symbols"] += len(msg.full_text)
        user["last_message"] = time.time()

    async def process_message(self, msg):
        if not msg.meta["data_chat"]:
            return await msg.answer("✋ Статистика в личных сообщениях не учитывается.")

        statistics = sorted(
            msg.meta["data_chat"]["chat_statistics"]["users"].items(),
            key=lambda item: (-item[1]["messages"], -item[1]["last_message"])
        )[:10]

        result = "👀 Немного статистики:\n"

        for i, pack in enumerate(statistics):
            uid, u = pack

            if uid == self.api.get_current_id():
                isbot = "(👾 бот) "
            else:
                isbot = ""

            result += f"{i + 1}. {isbot}" + await parse_user_name(uid, msg) + \
                f" (сообщений: {u['messages']}, символов: {u['symbols']}).\n"

        await msg.answer(result)
