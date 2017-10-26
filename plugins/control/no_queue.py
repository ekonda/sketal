import time

from handler.base_plugin import BasePlugin


class NoQueuePlugin(BasePlugin):
    __slots__ = ("users", "fail_time")

    def __init__(self, fail_time=10):
        """Forbids user to send messages to bot while his message is being processing by bot."""

        super().__init__()

        self.users = {}
        self.fail_time = fail_time

    async def global_before_message(self, msg, plugin):
        if len(self.users) > 2000:
            self.users.clear()

        if msg.user_id not in self.users:
            self.users[msg.user_id] = time.time()
            return True

        if time.time() - self.users[msg.user_id] > self.fail_time:
            del self.users[msg.user_id]

            return True

        return False

    async def global_after_message(self, msg, plugin, result):
        if msg.user_id in self.users:
            del self.users[msg.user_id]
