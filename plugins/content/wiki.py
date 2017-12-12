from handler.base_plugin_command import CommandPlugin

import aiohttp


class WikiPlugin(CommandPlugin):
    __slots__ = ()

    def __init__(self, *commands, prefixes=None, strict=False):
        """Asnwers with found data from wikipedia"""

        super().__init__(*commands, prefixes=prefixes, strict=strict)

        self.description = ["Википедия", f"{self.command_example()} [что-то] - получить информацию о чём-то"]

    async def process_message(self, msg):
        command, text = self.parse_message(msg, full_text=True)
        text = text.replace(" ", "+")

        url = f"https://ru.wikipedia.org/w/api.php?action=opensearch&search={text}&limit=1&format=json" \
              f"&prop=info&redirects=resolve"

        answer = ""

        async with aiohttp.ClientSession() as sess:
            async with sess.get(url) as resp:
                result = await resp.json()

                if not result or len(result) < 4:
                    return await msg.answer("Ничего не найдено!")

                length = len(result[1])

                for i in range(length):
                    try:
                        if result[2][i][-1] == ":":
                            answer += "Возможные значения: " + result[3][i] + "\n"

                        else:
                            answer += result[2][i] + "\n"
                            answer += "Подробнее: " + result[3][i] + "\n"

                            answer += "\n"

                    except Exception as e:
                        if self.bot.settings.DEBUG:
                            self.bot.logger.warning("WikiPlugin error: " + str(e))

                if not answer:
                    return await msg.answer("Ничего не найдено!")

                return await msg.answer(answer)
