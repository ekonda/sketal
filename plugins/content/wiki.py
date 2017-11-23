from handler.base_plugin_command import CommandPlugin

import aiohttp


class WikiPlugin(CommandPlugin):
    __slots__ = ()

    def __init__(self, *commands, prefixes=None, strict=False):
        super().__init__(*commands, prefixes=prefixes, strict=strict)

    async def process_message(self, msg):
        command, text = self.parse_message(msg, full_text=True)

        url = f"https://ru.wikipedia.org/w/api.php?action=opensearch&search={text}&limit=1&format=json" \
              f"&prop=info&redirects=resolve"

        answer = ""

        async with aiohttp.ClientSession() as sess:
            async with sess.get(url) as resp:
                result = await resp.json()

                if not result:
                    return await msg.answer("Ничего не найдено!")

                length = len(result[1])

                for i in range(length):
                    if result[2][i][-1] == ":":
                        answer += "Возможные значения: " + result[3][i] + "\n"

                    else:
                        answer += result[2][i] + "\n"
                        answer += "Подробнее: " + result[3][i] + "\n"

                    answer += "\n"

                return await msg.answer(answer)
