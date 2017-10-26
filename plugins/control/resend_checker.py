from handler.base_plugin import BasePlugin
from utils import traverse

from asyncio import ensure_future


class ResendCheckerPlugin(BasePlugin):
    __slots__ = ()

    def __init__(self):
        """Checks messages' forwarded messages for commands."""

        super().__init__()

    async def check_message(self, msg):
        return True

    async def process_message(self, msg):
        fwrd = traverse(await msg.get_full_forwarded())

        try:
            ensure_future(self.bot.handler.process(next(fwrd)))

        except StopIteration:
            pass
