import io
import requests
import time

from PIL import Image

from plugin_system import Plugin
import publicsuffixlist

psl = publicsuffixlist.PublicSuffixList()

plugin = Plugin('Зеркало', usage="отзеркаль <прикреплённые фото> - ")

FAIL_MSG = 'К сожалению, произошла какая-то ошибка :('


@plugin.on_command('отзеркаль')
async def mirror(msg, args):
    no_photo = True
    for k in msg.brief_attaches:
        if '_type' in k and msg.brief_attaches[k] == "photo":
            no_photo = False
            break

    if no_photo:
        return await msg.answer('Вы не прислали фото!')

    attach = (await msg.full_attaches)[0]
    response = requests.get(attach.link)
    img = Image.open(io.BytesIO(response.content))

    w, h = img.size

    part = img.crop((0, 0, w / 2, h))
    part1 = part.transpose(Image.FLIP_LEFT_RIGHT)
    img.paste(part1, (round(w / 2), 0))

    buffer = io.BytesIO()
    img.save(buffer, format='png')
    buffer.seek(0)

    result = await msg.vk.upload_photo(buffer)

    return await msg.answer('Держи', attachment=str(result))

