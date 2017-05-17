# Standart library
import asyncio
import hues

# Custom packages
import logging

from aiohttp import web

from database import *
from utils import MessageEventData
from vbot import Bot


class CallbackBot(Bot):
    CONF_CODE = ""  # Введите код подтверждения тут

    YOUR_IP = ""  # IP для сервера
    YOUR_PORT = ""  # Порт для сервера

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
            # Человек написал сообщение
            data = MessageEventData(False, 0, obj['user_id'], obj['body'], obj['date'],
                                    obj["id"], ["yes"] if obj["attachments"] else [])
            await self.check_if_command(data)
        if type == 'group_join':
            # Человек присоединился к группе
            uid = int(obj['user_id'])
            user = await db.get_or_create(uid=uid)
            user.in_group = True
            await db.update(user)

        if type == 'group_leave':
            # Человек вышел из группы
            uid = int(obj['user_id'])
            user = await db.get_or_create(uid=uid)
            user.in_group = False
            await db.update(user)

        # Возвращаем ответ, что всё ок
        return web.Response(text='ok')


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    bot = CallbackBot()
    app = web.Application(loop=loop)
    app.router.add_post('/', bot.process_callback)

    hues.success("Приступаю к приему сообщений")

    try:
        web.run_app(app, host=bot.YOUR_IP, port=bot.YOUR_PORT)
    except (KeyboardInterrupt, SystemExit):
        hues.warn("Выключение бота...")

    except Exception as ex:
        import traceback

        logging.warning("Fatal error:\n")
        traceback.print_exc()

        exit(1)
