import random
import tempfile

import aiohttp
import langdetect
from gtts import gTTS
from langdetect import DetectorFactory
from langdetect.lang_detect_exception import LangDetectException

from plugin_system import Plugin

ADDITIONAL_LANGUAGES = {
    'uk': 'Ukrainian',
}

gTTS.LANGUAGES.update(ADDITIONAL_LANGUAGES)

DetectorFactory.seed = 0

plugin = Plugin('Голос', usage=["скажи [выражение] - бот сформирует "
                                "голосовое сообщение на основе текста голосом Google",
                                "озвуч [выражение] - бот сформирует "
                                "голосовое сообщение на основе текста голосом Yandex"])

FAIL_MSG = 'Я не смог это произнести :('


@plugin.on_command('скажи')
async def say_text_google(msg, args):
    # Используется озвучка гугла gTTS
    try:
        text, lang = await args_validation(msg, args, 'google')
        tts = gTTS(text=text, lang=lang)
        # Сохраняем файл с голосом
        # TODO: Убрать сохранение (хранить файл в памяти)
        tts.save('audio.mp3')
        audio_file = open('audio.mp3', 'rb')
        await upload_voice(msg, audio_file)
    except ValueError:
        pass


@plugin.on_command('озвуч')
async def say_text_yandex(msg, args):
    # Используется озвучка яндекса. Класс yTTS
    try:
        text, lang = await args_validation(msg, args, 'yandex')
        tts = yTTS(text=text, lang=lang)
        tmp_file = await tts.save()
        audio_file = tmp_file.read()
        await upload_voice(msg, audio_file)
    except ValueError:
        pass


async def args_validation(msg, args=None, tts='google'):
    # Функция проверяет текст на соответствие правилам
    # Возвращает текст и язык сообщения или возбуждает исключение
    google_limit = 450
    yandex_limit = 2000

    if not args:
        await msg.answer('Вы не ввели сообщение!\nПример: скажи <текст>')
        raise ValueError

    text = ' '.join(args)
    text_length = google_limit if tts == 'google' else yandex_limit
    if len(text) > text_length:
        await msg.answer('Слишком длинное сообщение!')
        raise ValueError

    lang = get_lang(text)
    return text, lang


async def get_data(url, params=None):
    async with aiohttp.ClientSession() as sess:
        async with sess.get(url, data=params) as resp:
            if resp.status != 200:
                raise ValueError
            return await resp.read()


async def upload_voice(msg, audio_file):
    # Получаем URL для загрузки аудио сообщения
    upload_method = 'docs.getUploadServer'
    upload_server = await msg.vk.method(upload_method, {'type': 'audio_message'})
    url = upload_server.get('upload_url')
    if not url:
        return await msg.answer(FAIL_MSG)

    # Загружаем аудио через aiohttp
    form_data = aiohttp.FormData()
    form_data.add_field('file', audio_file)
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=form_data) as resp:
            file_url = await resp.json()
            file = file_url.get('file')
            if not file:
                return await msg.answer(FAIL_MSG + 'NOT_FILE')

    # Сохраняем файл в документы (чтобы можно было прикрепить к сообщению)
    saved_data = await msg.vk.method('docs.save', {'file': file})
    if not saved_data:
        return await msg.answer(FAIL_MSG)
    # Получаем первый элемент, так как мы сохранили 1 файл
    media = saved_data[0]
    media_id, owner_id = media['id'], media['owner_id']
    # Прикрепляем аудио к сообщению :)
    await msg.answer('', attachment=f'doc{owner_id}_{media_id}')


def get_lang(text):
    try:
        lang = langdetect.detect(text)
        if lang in ('mk', 'bg'):
            lang = 'ru'
    except LangDetectException:
        lang = 'ru'
    return lang


class yTTS(object):
    base_url = "https://tts.voicetech.yandex.net/tts"

    speakers = ["jane", "oksana", "alyss", "omazh", "zahar", "ermil"]
    emotion = ["good", "neutral", "evil"]

    def __init__(self, text, lang='ru_RU', **kwargs):
        # Инициализируем данные для запроса
        self.params = {
            "text": text,
            "lang": self.get_lang_name(lang),
            "emotion": random.choice(self.emotion),
            "speaker": random.choice(self.speakers),
            "speed": random.uniform(0.3, 1.5),
            "format": 'mp3',
        }
        if not kwargs.get('key'):
            pass
            # hues.info('Получите ключ в кабинете разработчика yandex cloud.')
        self.params.update(kwargs)

    async def save(self):
        # Возвращает объект временного файла. Асинхронно.
        tmp = tempfile.NamedTemporaryFile(suffix='.mp3')
        data = await get_data(self.base_url, self.params)
        with open(tmp.name, 'wb') as f:
            f.write(data)
        return tmp

    def save_file(self, name='test.mp3'):
        # Сохраняет в файл. Синхронно.
        import requests
        resp = requests.get(self.base_url, params=self.params, stream=True)
        resp.raise_for_status()
        with open(name, 'wb') as f:
            f.write(resp.content)
            for chunk in resp.iter_content(chunk_size=1024):
                f.write(chunk)

    @staticmethod
    def get_lang_name(lang):
        # Преобразует коды стран в понятный формат для yandex speech cloud
        # Яндекс поддерживает только 4 языка: RU, UK, EN, TR
        languages = {
            'en': 'en_US',
            'ru': 'ru_RU',
            'uk': 'uk_UK',
            'tr': 'tr_TR',
        }
        if lang in languages:
            return languages[lang]
        else:
            return languages['ru']


