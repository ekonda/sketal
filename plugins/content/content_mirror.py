import io
import aiohttp
from PIL import Image

from handler.base_plugin import CommandPlugin
from utils import upload_photo


class MirrorPlugin(CommandPlugin):
    __slots__ = ()

    def __init__(self, *commands, prefixes=None, strict=False):
        if not commands:
          commands = ("отзеркаль",)
        super().__init__(*commands, prefixes=prefixes, strict=strict)

        self.set_description()

    def set_description(self):
        example = self.command_example()
        self.description = ["Зеркало",
                            f"{example} <прикреплённые фото> - отзеркаливает прикреплённое фото"]

    async def process_message(self, msg):
        photo = None

        if msg.brief_attaches:
            for a in await msg.get_full_attaches():
                if a.type == "photo":
                    photo = a

        img = None

        if not photo or not photo.url:
            return await msg.answer("Вы не прислали фотографию.")

        if not img:
            async with aiohttp.ClientSession() as sess:
                async with sess.get(photo.url) as response:
                    img = Image.open(io.BytesIO(await response.read()))

        if not img:
            return await msg.answer('К сожалению, ваше фото исчезло!')

        w, h = img.size
        part = img.crop((0, 0, w / 2, h))
        part1 = part.transpose(Image.FLIP_LEFT_RIGHT)
        img.paste(part1, (round(w / 2), 0))


        f = io.BytesIO()
        img.save(f, format='png')
        f.seek(0)
        attachment = await upload_photo(self.bot.api, f, msg.user_id)
        f.close()

        return await msg.answer("Готово", attachment=str(attachment))
