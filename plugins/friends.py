import asyncio
import hues

from plugin_system import Plugin
from utils import schedule_coroutine
from settings import ACCEPT_FRIENDS

if ACCEPT_FRIENDS:
    plugin = Plugin("Автоматическое добавление друзей(каждые 10 секунд)")

    @plugin.on_init()
    async def get_vk(vk):
        if vk.user_api:
            schedule_coroutine(add_friends(vk))

    # Функция, если её запустить(см. get_vk для примера с выполнением в фоне),
    # будет выполняться каждые 10 секунд, до тех пор, пока stopper.stop == False
    #
    # Функция обязана принимать 1 обязательны параметр - stopper, но может
    # принимать и больше
    @plugin.schedule(10)
    async def add_friends(stopper, vk):
        result = await vk.method("friends.getRequests")

        if not result or not result["count"]:
            return

        users = result["items"]

        for user in users:
            await vk.method("friends.add", {"user_id": user})