import time

from handler.base_plugin import BasePlugin


class AntifloodPlugin(BasePlugin):
    __slots__ = ("users", "delay")

    def __init__(self, delay=1.1):
        """ Forbids users to send messages to bot more often than delay `delay`.
        If `absolute` is True, bot wont answer on more than 1 message in delay
        time."""
        super().__init__()
        self.order = (-85, 85)

        self.users = {}
        self.delay = delay

    async def global_before_message_checks(self, msg):
        current_time = time.time()

        if msg.meta.get("data_user"):
            last_message = msg.meta["data_user"].getraw("last_message", 0)

            if current_time - last_message <= self.delay:
                return False

            msg.meta["data_user"]["last_message"] = current_time

        else:
            if len(self.users) > 5000:
                self.users.clear()

            if current_time - self.users.get(msg.user_id, 0) <= self.delay:
                return False

            self.users[msg.user_id] = current_time
