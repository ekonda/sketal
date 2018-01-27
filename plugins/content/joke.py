from handler.base_plugin_command import CommandPlugin

import aiohttp, time, json, re
#AMAZING SITE: http://nextjoke.net


class JokePlugin(CommandPlugin):
    __slots__ = ()

    def __init__(self, *commands, prefixes=None, strict=False):
        if not commands:
            commands = ["анекдот", "а", "f"]

        super().__init__(*commands, prefixes=prefixes, strict=strict)

    async def process_message(self, msg):
        command, text = self.parse_message(msg)

        async with aiohttp.ClientSession() as sess:
            async with sess.get(f"http://nextjoke.net/Api/GetJoke?format=JSONP&ratingMin=100&NOCACHE={time.time()}") as resp:
                html = await resp.text()
                try:
                    html = json.loads(html.replace("window.JokeWidget.parseResponse(", "", 1)[:-2])["text"]
                except (KeyError, json.decoder.JSONDecodeError):
                    return await msg.answer("Сегодня без шуток ;(")

                html = re.sub("(\n|^| )-([A-Za-zА-Яа-я])", "- \\2", html)

        return await msg.answer(html.replace("\r", ""))
