from handler.base_plugin import CommandPlugin
from utils import upload_audio_message

from gtts import gTTS
import langdetect

from random import choice
import asyncio, aiohttp, io


class SayerPlugin(CommandPlugin):
    __slots__ = ("key", "providers")

    def __init__(self, *commands, key=None, use_yandex=True, prefixes=None, strict=False):
        """Answers with audio message of user's text"""

        if not commands:
            commands = ("скажи", "произнеси")

        super().__init__(*commands, prefixes=prefixes, strict=strict)

        self.key = key
        self.providers = [(lambda text, lang, key=None: gTTS(text=text, lang=lang)),
            (lambda text, lang, key=None: yTTS(text=text, lang=lang, key=key)),]

        if use_yandex:
            self.providers[0], self.providers[1] = self.providers[1], self.providers[0]

        example = self.command_example()
        self.description = [f"Текст в речь",
            f"{example} [текст] - произнести текст (+ значит ударение перед ударной гласной)."]

    def initiate(self):
        if not self.key:
            self.bot.logger.warning("No key specified for Yandex Speechkit Cloud. Google "
                "will be used. You can get your key - https://tech.yandex.ru/speechkit/cloud/.")

    @staticmethod
    def get_lang(text):
        resu = None

        try:
            langs = langdetect.detect_langs(text)

            for language in langs:
                if language.lang == "ru":
                    language.prob += 0.2

                if resu is None or resu < language:
                    resu = language

        except langdetect.lang_detect_exception.LangDetectException:
            pass

        if resu is None:
            return "ru"

        return resu.lang

    async def create_audio(self, provider, text):
        if len(text) > 500:
            return "Слишком длинное сообщение", None

        try:
            lang = self.get_lang(text)

            for provider in self.providers:
                tts = provider(text, lang, self.key)

                f = io.BytesIO()

                if asyncio.iscoroutinefunction(tts.write_to_fp):
                    await tts.write_to_fp(f)
                else:
                    tts.write_to_fp(f)

                f.seek(0)

                if f.getbuffer().nbytes < 16:
                    f.close()
                    continue

                return "", f

        except ValueError:
            pass

        return "Произошла ошибка! Попробуйте позже.", None

    async def process_message(self, msg):
        command, text = self.parse_message(msg, full=True)

        if not text:
            return await msg.answer('Введите текст для перевода его в речь!')

        answer, answer_file = await self.create_audio(gTTS, text)

        if answer_file is None:
            return await msg.answer(answer)

        audio = await upload_audio_message(self.api, answer_file, msg.user_id)
        answer_file.close()

        return await msg.answer("", attachment=str(audio))


class yTTS(object):
    __slots__ = ("params",)

    base_url = "https://tts.voicetech.yandex.net/tts"

    speakers = ["jane", "oksana", "alyss", "omazh", "zahar", "ermil"]
    emotion = ["good", "neutral", "evil"]
    languages = {'en': 'en_US', 'ru': 'ru_RU', 'uk': 'uk_UK', 'tr': 'tr_TR'}

    def __init__(self, text, lang='ru_RU', key=""):
        self.params = {
            "text": text,
            "lang": self.languages.get(lang, "ru_RU"),
            "emotion": choice(self.emotion),
            "speaker": choice(self.speakers),
            "speed": "0.8",
            "format": 'mp3',
        }

        if key:
            self.params[key] = key

    async def write_to_fp(self, f):
        try:
            return await self._write_to_fp(f)
        except Exception:
            return False

    async def _write_to_fp(self, f):
        async with aiohttp.ClientSession(raise_for_status=True) as sess:
            async with sess.get(self.base_url, params=self.params) as resp:
                while True:
                    chunk = await resp.content.read(1024)

                    if not chunk:
                        break

                    f.write(chunk)

        return True
