from handler.base_plugin_command import CommandPlugin

import urllib
import aiohttp


class TranslatePlugin(CommandPlugin):
    __slots__ = ("key", "pair", "commands")

    def __init__(self, *commands, prefixes=None, strict=False, pair=("en", "ru"), key=None):
        """Answers with translated text from english to russian or from russian to english

        You can change language pair by passing list of 2 names of desired languages (https://tech.yandex.ru/translate/)"""

        if key is None:
            raise AttributeError("No key specified! https://tech.yandex.ru/translate/")

        super().__init__(*commands, prefixes=prefixes, strict=strict)

        self.key = key
        self.pair = pair
        self.commands = commands if commands else "переведи"

        example = self.command_example()
        self.description = [f"Переводчик",
                            f"{example} [тест] - тепевести текст с языка \"{pair[0]}\" на \"{pair[1]}\" или наоборот."]

    def check_code(self, result):
        if "code" not in result:
            return "Неизвестная ошибка! Попробуй позже!"

        if result["code"] in (404, 402, 401):
            self.bot.logger.error("Перевод вернулся с кодом: " + str(result["code"]))

            return "Бот уже перевёл слишком много текстов! Попробуй завтра."

        if result["code"] != 200:
            return "Текст не может быть переведён."

        return "ok"

    async def process_message(self, msg):
        command, text = self.parse_message(msg, full_text=True)

        if not text:
            return await msg.answer("Введите текст!")

        url_text = urllib.parse.quote_plus(text)

        url_l = f"https://translate.yandex.net/api/v1.5/tr.json/detect?key={self.key}&text={url_text}"

        async with aiohttp.ClientSession() as sess:
            async with sess.get(url_l) as resp:
                result = await resp.json()

                check = self.check_code(result)

                if check != "ok":
                    return await msg.answer(check)

                language = result["lang"]

        language = self.pair[1] if language == self.pair[0] else self.pair[0]

        url = f"https://translate.yandex.net/api/v1.5/tr.json/translate?key={self.key}&text={url_text}" \
              f"&lang={language}"

        async with aiohttp.ClientSession() as sess:
            async with sess.get(url) as resp:
                result = await resp.json()

                check = self.check_code(result)

                if check != "ok":
                    return await msg.answer(check)

                return await msg.answer("\n".join(result["text"]))
