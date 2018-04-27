from handler.base_plugin import CommandPlugin
from vkutils import upload_photo
from utils import traverse, timestamp_to_date

from PIL import Image, ImageDraw, ImageFont

import aiohttp, io


class QuoteDoerPlugin(CommandPlugin):
    __slots__ = ("q", "qf", "f", "fs", "fss")

    def __init__(self, *commands, prefixes=None, strict=False):
        """Answers with image containing stylish quote."""

        if not commands:
            commands = ("цитата",)

        super().__init__(*commands, prefixes=prefixes, strict=strict)

        self.q = Image.open(self.get_path("q.png")).resize((40, 40), Image.LANCZOS)
        self.qf = self.q.copy().transpose(Image.FLIP_LEFT_RIGHT).transpose(Image.FLIP_TOP_BOTTOM)

        self.f = ImageFont.truetype(self.get_path("font.ttf"), 24)
        self.fs = ImageFont.truetype(self.get_path("font.ttf"), 16)
        self.fss = ImageFont.truetype(self.get_path("font.ttf"), 16)

        example = self.command_example()
        self.description = [f"Генератор цитат",
                            f"{example} [титул] - перешлите сообщение и укажите титул (по желанию) и "
                             "получите цитату!"]

    async def process_message(self, msg):
        command, otext = self.parse_message(msg)

        i, url, name, last_name, timestamp = None, None, None, None, None

        for m in traverse(await msg.get_full_forwarded()):
            if m.full_text:
                if i == m.true_user_id:
                    text += "\n" + m.full_text
                    continue
                elif i is not None:
                    break

                i = m.true_user_id
                timestamp = m.timestamp

                u = await self.api.users.get(user_ids=i, fields="photo_max")
                if not u:
                    continue

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
                img = img.resize((200, 200), Image.NEAREST)

        rsize = (700, 400)

        res = Image.new("RGB", rsize, color=(0, 0, 0))
        res.paste(img, (25, 100))

        tex = Image.new("RGB", rsize, color=(0, 0, 0))
        draw = ImageDraw.Draw(tex)

        if len(text) > 70:
            font = self.fss
        else:
            font = self.f

        sidth = int(draw.textsize(" ", font=font)[0])

        width, height = 0, 0
        new_text = ""

        for line in text.splitlines():
            for word in line.split():
                word_width = len(word) * sidth

                if width + word_width >= rsize[0] - 340:
                    width = 0
                    new_text += "\n"

                width += sidth + word_width
                new_text += word + " "

            width = 0
            new_text += "\n"

        new_text = new_text[:-1]

        width, height = draw.multiline_textsize(new_text, font=font)
        draw.multiline_text((0, 0), new_text, font=font)

        y = rsize[1] // 2 - height // 2
        x = 300 + (rsize[0] - 370 - width) // 2

        res.paste(tex, (x, y))

        if y <= 10:
            return await msg.answer("Не получилось... простите.")

        if height < 210:
            height = 210
            y = rsize[1] // 2 - height // 2

        res.paste(self.q, (240, y))
        res.paste(self.qf, (rsize[0] - 65, y + height - 40))

        draw = ImageDraw.Draw(res)
        draw.multiline_text((25, 310), f"© {name} {last_name}{' - ' + otext if otext else ''}"
            f"\n@ {timestamp_to_date(timestamp)}", font=self.fs)

        buff = io.BytesIO()
        res.save(buff, format='png')

        attachment = await upload_photo(self.api, buff.getvalue(), msg.user_id)

        return await msg.answer(attachment=str(attachment))
