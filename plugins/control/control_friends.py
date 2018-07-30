import asyncio

from handler.base_plugin import BasePlugin


class FriendsPlugin(BasePlugin):
    __slots__ = ("accepter",)

    def __init__(self):
        """Accepts friend requests once in a minute."""
        super().__init__()

    def initiate(self):
        async def runner():
            while True:
                await asyncio.sleep(5)
                await self.accept_friends()

        self.accepter = asyncio.ensure_future(runner())

    async def accept_friends(self):
        requests = await self.api.friends.getRequests()

        if not requests:
            return

        for user_id in requests["items"]:
            await self.api.friends.add(user_id=user_id)
