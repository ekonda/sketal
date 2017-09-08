# Standart library
import logging
from os import getenv

import hues
from aiohttp import web
import asyncio

from database import *
from utils import MessageEventData
from vbot import Bot


class CallbackBot(Bot):
    CONF_CODE = ""  # Введите код подтверждения тут

    async def process_callback(self, request):
        """Функция для обработки запроса от VK Callback API группы"""
        try:
            data = await request.json()
        except Exception:
            # Почти невозможно, что будет эта ошибка
            return web.Response(text="ok")

        type = data['type']
        if type == 'confirmation':
            # Нам нужно подтвердить наш сервер
            return web.Response(text=self.CONF_CODE)
        obj = data['object']

        if type == 'message_new':
            uid = int(obj['user_id'])

            data = MessageEventData(False, 0, uid, obj['body'], obj['date'],
                                    obj["id"], ["yes"] if ("attachments" in obj) else [])

            user, create = await db.get_or_create(User, uid=uid)

            await self.check_if_command(data, user)
        if type == 'group_join':
            # Человек присоединился к группе
            uid = int(obj['user_id'])

            user, create = await db.get_or_create(uid=uid)

            user.in_group = True

            await db.update(user)

        if type == 'group_leave':
            # Человек вышел из группы
            uid = int(obj['user_id'])

            user, create = await db.get_or_create(uid=uid)

            user.in_group = False

            await db.update(user)

        return web.Response(text='ok')


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    bot = CallbackBot()
    app = web.Application(loop=loop)
    app.router.add_post('/', bot.process_callback)

    hues.success("Приступаю к приему сообщений")

    try:
        IP = getenv('IP', '0.0.0.0')
        PORT = int(getenv('PORT', 8000))

        web.run_app(app, host=IP, port=PORT)
    except (KeyboardInterrupt, SystemExit):
        hues.warn("Выключение бота...")

    except Exception as ex:
        import traceback

        logging.warning("Fatal error:\n")
        traceback.print_exc()

        exit(1)
