from handler.base_plugin_command import CommandPlugin
from vk.helpers import upload_photo
from utils import traverse

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

import aiohttp
import datetime, io


class QuotePlugin(CommandPlugin):
    __slots__ = ("q", "qf", "f", "fs")

    def __init__(self, *commands, prefixes=None, strict=False):
        """Answers with image containing stylish quote."""

        super().__init__(*commands, prefixes=prefixes, strict=strict)

        self.q = Image.open(self.get_path("q.png")).resize((40, 40), Image.LANCZOS)
        self.qf = self.q.copy().transpose(Image.FLIP_LEFT_RIGHT).transpose(Image.FLIP_TOP_BOTTOM)

        self.f = ImageFont.truetype(self.get_path("font.ttf"), 20)
        self.fs = ImageFont.truetype(self.get_path("font.ttf"), 14)

        example = self.command_example()
        self.description = [f"Генератор цитат",
                            f"{example} [титул] - перешлите сообщение и укажите титул (по желанию) и "
                             "получите цитату!"]

    async def process_message(self, msg):
        command, otext = self.parse_message(msg)

        i, url, name, last_name = None, None, None, None

        for m in traverse(await msg.get_full_forwarded()):
            if m.full_text:
                if i == m.true_user_id:
                    text += "\n" + m.full_text
                    continue
                elif i is not None:
                    break

                i = m.true_user_id

                u = await self.api.users.get(user_ids=i, fields="photo_max")
                if not u: continue
                u = u[0]

                url = u["photo_max"]
                name = u["first_name"]
                last_name = u["last_name"]

                text = m.full_text
        else:
            if i is None:
                return await msg.answer("Нечего цитировать!")

        async with aiohttp.ClientSession() as sess:
            async with sess.get(url) as response:
                img = Image.open(io.BytesIO(await response.read()))
                img = img.resize((200, 200))

        rsize = (700, 400)
        res = Image.new("RGBA", rsize, color=(0, 0, 0))
        res.paste(img, (25, 100))

        tex = Image.new("RGBA", rsize, color=(0, 0, 0))

        draw = ImageDraw.Draw(tex)

        sidth = draw.textsize(" ", font=self.f)[0]
        seight = int(draw.textsize("I", font=self.f)[1] * 1.05)

        text = text.splitlines()

        midth = 0
        width = 0
        height = 0
        for line in text:
            for word in line.split(" "):
                size = draw.textsize(word, font=self.f)

                if width + size[0] >= rsize[0] - 340:
                    height += seight
                    width = 0

                draw.text((width, height), word, font=self.f)
                width += sidth + size[0]

                if width > midth:
                    midth = width

            height += seight
            width = 0

        y = rsize[1] // 2 - height // 2
        x = 300 + (rsize[0] - 370 - midth) // 2
        res.alpha_composite(tex, (x, y))

        if height < 210:
            height = 210
            y = rsize[1] // 2 - height // 2

        res.alpha_composite(self.q, (250, y + 10))
        res.alpha_composite(self.qf, (rsize[0] - 75, y + int(height - seight * 2 + 10)))

        draw = ImageDraw.Draw(res)
        draw.multiline_text((25, 310), f"© {name} {last_name}{' - ' + otext if otext else ''}\n"
                                       f"@ {datetime.date.today()}", font=self.fs)

        f = io.BytesIO()
        res.save(f, format='png')
        f.seek(0)
        attachment = await upload_photo(self.api, f, msg.user_id)
        f.close()

        return await msg.answer('', attachment=str(attachment))
