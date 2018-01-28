from handler.base_plugin_command import CommandPlugin
from vk.helpers import upload_photo

import io

import qrcode
from qrcode.exceptions import DataOverflowError

class QRCodePlugin(CommandPlugin):
    __slots__ = ()

    def __init__(self, *commands, prefixes=None, strict=False):
        """Answers with encoded and QR code data specified in command"""

        super().__init__(*commands, prefixes=prefixes, strict=strict)

        example = self.command_example()
        self.description = [f"QR Кодировщик",
                            f"{example} [тест / ссылка] - закодировать текст или ссылку."]

    async def process_message(self, msg):
        command, text = self.parse_message(msg, full_text=True)

        if not text:
            await msg.answer('Введите слова или ссылку чтобы сгенерировать QR код')

        qr = qrcode.QRCode(
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )

        qr.add_data(text)

        try:
            qr.make(fit=True)
        except DataOverflowError:
            return await msg.answer('Слишком длинное сообщение!')

        img = qr.make_image()

        buffer = io.BytesIO()
        img.save(buffer, format='png')
        buffer.seek(0)

        result = await upload_photo(self.api, buffer)

        return await msg.answer(f'Ваш QR код, с данными: \n "{msg.text}"', attachment=str(result))
