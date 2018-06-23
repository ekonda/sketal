from handler.base_plugin import CommandPlugin
from utils import upload_photo

import io

import qrcode
from qrcode.exceptions import DataOverflowError

class QRCodePlugin(CommandPlugin):
    __slots__ = ()

    def __init__(self, *commands, prefixes=None, strict=False):
        """Answers with encoded and QR code data specified in command"""

        if not commands:
            commands = ("куер", "qr")

        super().__init__(*commands, prefixes=prefixes, strict=strict)

        example = self.command_example()
        self.description = [f"QR Кодировщик",
                            f"{example} [тест / ссылка] - закодировать текст или ссылку."]

    async def process_message(self, msg):
        command, text = self.parse_message(msg, full=True)

        if not text:
            await msg.answer('Введите слова или ссылку чтобы сгенерировать QR код')

        qr = qrcode.QRCode(
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )

        qr.add_data(text)

        try:
            result = await self.run_in_executor(lambda: qr.make(fit=True))
        except DataOverflowError:
            return await msg.answer('Слишком длинное сообщение!')

        img = await self.run_in_executor(qr.make_image)

        if not img:
            return await msg.answer("Произошла ошибка!")

        buf = io.BytesIO()
        img.save(buf, format='png')
        buf.seek(0)

        result = await upload_photo(self.api, buf)

        return await msg.answer(f'Ваш QR код, с данными: \n "{text}"', attachment=str(result))
