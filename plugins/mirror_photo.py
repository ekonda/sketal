import io
import requests

from PIL import Image

from plugin_system import Plugin
import publicsuffixlist

psl = publicsuffixlist.PublicSuffixList()

plugin = Plugin('Зеркало', usage="отзеркаль <прикреплённые фото> - ")

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

