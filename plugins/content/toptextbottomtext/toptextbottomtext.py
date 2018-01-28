from handler.base_plugin_command import CommandPlugin
from vk.helpers import upload_photo

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

import aiohttp
import io


class ToptextbottomtextPlugin(CommandPlugin):
    __slots__ = ("fonts", "sizes", "allow_photos", "default_photo")

    def __init__(self, *commands, prefixes=None, strict=False, font="Impact.ttf",
                 image="Default.jpg", allow_photos=True):
        """Answers with picture with custom text on."""

        super().__init__(*commands, prefixes=prefixes, strict=strict)

        self.allow_photos = allow_photos

        with open(self.get_path(image), "rb") as f:
            self.default_photo = f.read()

        self.sizes = [400, 300, 200, 100, 90, 70, 60, 50, 40, 30, 20]

        self.fonts = []

        path = self.get_path(font)

        for size in self.sizes:
            self.fonts.append(ImageFont.truetype(path, size))

        example = self.command_example()
        self.description = [f"Генератор картинкок с текстом",
                            f"{example} [верхний текст]\n[нижний текст] - тексты для картинки "
                             "(на разных строчках, необязательно оба)."]

        if self.allow_photos:
            self.description.append("Вы можете присылать свои картинки для текста! Просто приложите её к сообщению.")

    async def process_message(self, msg):
        command, text = self.parse_message(msg)

        if not text:
            return await msg.answer("Пожалуйста, укажите текст(ы) для картинки!")

        photo = None

        if msg.brief_attaches and self.allow_photos:
            for a in await msg.get_full_attaches():
                if a.type == "photo":
                    photo = a

        img = None

        if not photo or not photo.url:
            img = Image.open(io.BytesIO(self.default_photo))

        if not img:
            async with aiohttp.ClientSession() as sess:
                async with sess.get(photo.url) as response:
                    img = Image.open(io.BytesIO(await response.read()))

        if not img:
            return await msg.answer('К сожалению, ваше фото исчезло!')

        strings = text.upper().split("\n")

        if len(strings) < 2:
            strings += [""]

        if strings[0] == "":
            strings[0] = " "

        left_font = 0
        right_font = len(self.fonts)

        max_h = 0.15
        max_w = 0.9

        fits = False

        while right_font - left_font > 1:
            current_font = (right_font + left_font) // 2

            font = self.fonts[current_font]

            top_text_size = font.getsize(strings[0])
            bottom_text_size = font.getsize(strings[1])

            if top_text_size[0] >= img.size[0] * max_w or top_text_size[1] >= img.size[1] * max_h \
                    or bottom_text_size[0] >= img.size[0] * max_w or bottom_text_size[1] >= img.size[1] * max_h:
                left_font = current_font
            else:
                fits = True

                right_font = current_font

        if fits:
            font = self.fonts[right_font]
            top_text_size = font.getsize(strings[0])
            bottom_text_size = font.getsize(strings[1])

        else:
            return await msg.answer("Ваш текст не влезает! Простите!")

        top_text_position = img.size[0] / 2 - top_text_size[0] / 2, 0
        bottom_text_position = img.size[0] / 2 - bottom_text_size[0] / 2, img.size[1] - bottom_text_size[1] * 1.17

        draw = ImageDraw.Draw(img)

        outline_range = int(top_text_size[1] * 0.12)
        for x in range(-outline_range, outline_range + 1, 2):
            for y in range(-outline_range, outline_range + 1, 2):
                draw.text((top_text_position[0] + x, top_text_position[1] + y),
                            strings[0], (0, 0, 0), font=font)

                draw.text((bottom_text_position[0] + x, bottom_text_position[1] + y),
                            strings[1], (0, 0, 0), font=font)

        draw.text(top_text_position, strings[0], (255, 255, 255), font=font)
        draw.text(bottom_text_position, strings[1], (255, 255, 255), font=font)

        f = io.BytesIO()
        img.save(f, format='png')
        f.seek(0)
        attachment = await upload_photo(self.bot.api, f, msg.user_id)
        f.close()

        return await msg.answer('Результат:', attachment=str(attachment))
