from handler.base_plugin_command import CommandPlugin

from vk.helpers import upload_photo
import aiohttp, random, string

BASE_API_URL = 'https://node-01.faceapp.io/api/v2.3/photos'  # Ensure no slash at the end.
BASE_HEADERS = {'User-agent': "FaceApp/1.0.229 (Linux; Android 4.4)"}
DEVICE_ID_LENGTH = 8
KNOWN_FILTERS = ['smile', 'smile_2', 'hot', 'old', 'young', 'female', 'male']
# Thanks to https://github.com/vasilysinitsin/Faces

class FacePlugin(CommandPlugin):
    __slots__ = ("filters")

    def __init__(self, *commands, prefixes=None, strict=False):
        super().__init__(*commands, prefixes=prefixes, strict=strict)

        self.filters = {
            'улыбка2': 'smile_2',

            'весёлой': 'smile',
            'весёлым': 'smile',
            'весело': 'smile',

            'старым': 'old',
            'старой': 'old',

            'молодым': 'young',
            'молодой': 'young',

            'мужчиной': 'male',
            'мужиком': 'male',
            'парнем': 'male',
            'поцем': 'male',

            'женщиной': 'female',
            'тёлкой': 'female',
            'тётей': 'female',
            'кисой': 'female',
        }

    @staticmethod
    def _generate_device_id():
        device_id = ''.join(random.choice(string.ascii_letters) for _ in range(DEVICE_ID_LENGTH))
        return device_id

    @staticmethod
    def _generate_headers(device_id):
        BASE_HEADERS.update({'X-FaceApp-DeviceID': device_id})
        return BASE_HEADERS

    async def process_message(self, msg):
        command, text = self.parse_message(msg)
        if not text or text not in self.filters.keys():
            return await msg.answer('🙋‍♂️ Список доступных фильтров:\n' + ", ".join(self.filters) + '\nВведите !лицо <фильтр> <прикрепленная фотография>')

        if not any(k.endswith('_type') and v == "photo"
            for k, v in msg.brief_attaches.items()):
                return await msg.answer('Вы не прислали фото!\nВведите \
                    !лицо <фильтр> <прикрепленная фотография>')

        photo_url = None
        for a in await msg.get_full_attaches():
            if a.type == "photo" and a.url:
                photo_url = a.url
                break
        else:
            return await msg.answer('Произошла какая-то ошибка. Попробуйте другу фотографию.')

        await msg.answer("Одну секундочку...")

        image = None
        async with aiohttp.ClientSession() as sess:
            async with sess.get(photo_url) as resp:
                image = await resp.read()

        if image is None:
            return await msg.answer("Ерунда какая-то! Ошибка...")

        device_id = self._generate_device_id()
        headers = self._generate_headers(device_id)

        code = None
        async with aiohttp.ClientSession() as sess:
            async with sess.post(BASE_API_URL, headers=headers, data={'file': image}) as resp:
                try:
                    response = await resp.json()
                except ValueError:
                    response = None

                code = response.get('code')

                if code is None:
                    error = resp.headers.get('X-FaceApp-ErrorCode')

                    if error == 'photo_bad_type':
                        return await msg.answer("Плохая у тебя картинка, пф")
                    elif error == 'photo_no_faces':
                        return await msg.answer("Не вижу лиц \\_C:_/")

                    return await msg.answer("Хм... Ошибка...")

        filter_name = text.strip().lower()
        filter_name = self.filters.get(filter_name, filter_name)

        if filter_name in ('male', 'female'):
            cropped = 1
        else:
            cropped = 0

        async with aiohttp.ClientSession() as sess:
            async with sess.get(
                    '{0}/{1}/filters/{2}?cropped={3}'.format(
                        BASE_API_URL, code, filter_name, cropped
                    ), headers=headers) as resp:
                image = await resp.read()
                error = resp.headers.get('X-FaceApp-ErrorCode')

                if error:
                    if error == 'bad_filter_id':
                        return await msg.answer("Какой-то фильтр у тебя неправильный очень...")
                    else:
                        return await msg.answer("Чо... Я сломался :(")

                at = await upload_photo(self.api, image)
                if not at:
                    return await msg.answer("Не удалось отправить картинку!")

                return await msg.answer(";)", attachment=at)
