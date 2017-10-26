from handler.base_plugin import BasePlugin


class ResendCommanderPlugin(BasePlugin):
    __slots__ = ()

    def __init__(self):
        """Forwards command with it's answer."""

        super().__init__()

    async def global_before_message(self, msg, plugin):
        if self.bot.settings.READ_OUT:
            return True

        msg.answer_values["forward_messages"] = msg.msg_id

        return True
