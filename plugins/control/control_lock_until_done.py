import time

from handler.base_plugin import BasePlugin


class NoQueuePlugin(BasePlugin):
    __slots__ = ("users", "fail_time")

    def __init__(self, fail_time=10):
        """Forbids user to send messages to bot while his message is being processing by bot."""
        super().__init__()

        self.order = (-87, 87)

        self.users = {}
        self.fail_time = fail_time

    async def global_before_message_checks(self, msg):
        current_time = time.time()

        if len(self.users) > 5000:
            self.users.clear()

        if msg.user_id not in self.users:
            self.users[msg.user_id] = current_time
            return

        if current_time - self.users[msg.user_id] >= self.fail_time:
            del self.users[msg.user_id]
            return

        return False

    async def global_after_message_process(self, msg, result):
        if msg.user_id in self.users:
            del self.users[msg.user_id]
