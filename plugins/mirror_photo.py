import io

import aiohttp
from PIL import Image

from plugin_system import Plugin

plugin = Plugin('Зеркало', usage=["отзеркаль <прикреплённые фото> - отзеркаливает прикреплённое фото"])

FAIL_MSG = 'К сожалению, произошла какая-то ошибка :('


@plugin.on_command('отзеркаль')
async def mirror(msg, args):
    photo = False
    for k, v in msg.brief_attaches.items():
        if '_type' in k and v == "photo":
            photo = True
            break

    if not photo:
        return await msg.answer('Вы не прислали фото!')

    attach = (await msg.full_attaches)[0]

    if not attach.link:
        return await msg.answer('Вы не прислали фото!')

    async with aiohttp.ClientSession() as sess:
        async with sess.get(attach.link) as response:
            img = Image.open(io.BytesIO(await response.read()))

    if not img:
        return await msg.answer('К сожалению, ваше фото исчезло!')

    w, h = img.size

    part = img.crop((0, 0, w / 2, h))
    part1 = part.transpose(Image.FLIP_LEFT_RIGHT)
    img.paste(part1, (round(w / 2), 0))

    buffer = io.BytesIO()
    img.save(buffer, format='png')
    buffer.seek(0)

    result = await msg.vk.upload_photo(buffer)

    return await msg.answer('Держи', attachment=str(result))

