import time

from handler.base_plugin import BasePlugin


class AntifloodPlugin(BasePlugin):
    __slots__ = ("users", "delay", "absolute", "absolute_time")

    def __init__(self, delay=1, absolute=False):
        """ Forbids users to send messages to bot more often than delay `delay`. If `absolute` is True, bot
        wont answer on more than 1 message in delay time.
        """

        super().__init__()

        self.users = {}

        self.delay = delay

        self.absolute = absolute
        self.absolute_time = 0

    async def global_before_message(self, msg, plugin):
        if len(self.users) > 2000:
            self.users.clear()

        ct = time.time()

        if self.absolute:
            if ct - self.absolute_time <= self.delay:
                return False

            self.absolute_time = ct

            return True

        else:
            if ct - self.users.get(msg.user_id, 0) <= self.delay:
                return False

            self.users[msg.user_id] = ct

            return True
