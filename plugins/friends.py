import asyncio
import hues

from plugin_system import Plugin
from settings import ACCEPT_FRIENDS

if ACCEPT_FRIENDS:
    plugin = Plugin("Автоматическое добавление друзей(каждые 10 секунд)")

    @plugin.on_init()
    async def get_vk(vk):
        asyncio.ensure_future(add_friends(vk))

    @plugin.schedule(10)
    async def add_friends(vk):
        result = await vk.method("friends.getRequests")

        if not result["count"]:
            return

        users = result["items"]

        for user in users:
            await vk.method("friends.add", {"user_id": user})