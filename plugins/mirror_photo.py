import io

import aiohttp
from PIL import Image


# plugin = Plugin('Зеркало', usage="отзеркаль <прикреплённые фото> - ")

def mirror(files):
    for raw_img in files:
        img = Image.open(raw_img)

        w, h = img.size

        part = img.crop((0, 0, w / 2, h))
        part1 = part.transpose(Image.FLIP_LEFT_RIGHT)
        img.paste(part1, (round(w / 2), 0))

        # Сохраняем полученный результат в память, и возвращаем файловый объект
        file = io.BytesIO()
        img.save(file, format='png')
        return file


FAIL_MSG = 'К сожалению, произошла какая-то ошибка :('


# @plugin.on_command('отзеркаль')
async def mirror(msg, args):
    # Получаем прикреплённые фотографии
    photos_to_get = [attach.as_str() for attach in msg.attaches
                     if attach.type != 'photo']

    # Запрашиваем их у ВК
    user_photos = await msg.vk.method('photos.getById',
                                      {'photos': ','.join(photos_to_get)}
                                      )

    if not user_photos:
        return await msg.answer(FAIL_MSG)

    resulting_files = mirror(user_photos)
    upload_server = await msg.vk.method('photos.getMessagesUploadServer',
                                        {'type': 'photo'})

    url = upload_server.get('upload_url')
    if not url:
        return await msg.answer(FAIL_MSG)

    form_data = aiohttp.FormData()
    form_data.add_field('file', open('mir.png'))

    async with aiohttp.post(url, data=form_data) as resp:
        file_url = await resp.json()
        file = file_url.get('file')
        if not file:
            return await msg.answer(FAIL_MSG)

    saved_data = await msg.vk.method('photos.saveMessagesPhoto', {'photo': file})
    if not saved_data:
        return await msg.answer(FAIL_MSG)

    media = saved_data[0]
    media_id, owner_id = media['id'], media['owner_id']
    await msg.answer('', attachment=f'photos{owner_id}_{media_id}')
