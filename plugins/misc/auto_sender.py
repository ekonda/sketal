from handler.base_plugin import BasePlugin


class AutoSender(BasePlugin):
    __slots__ = ("text", )

    def __init__(self, text):
        """Answers with text `text` to user without any conditions."""

        super().__init__()

        self.text = text

    async def check_message(self, msg):
        return True

    async def process_message(self, msg):
        await msg.answer(self.text)
