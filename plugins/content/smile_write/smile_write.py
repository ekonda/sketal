from handler.base_plugin_command import CommandPlugin

import json


class SmileWritePlugin(CommandPlugin):
    __slots__ = ("data", "smiles", "max_chars")

    def __init__(self, *commands, prefixes=None, max_chars=20, smiles=("🌝", "🌚"), strict=False):
        if not commands:
            commands = ["смайлами"]

        super().__init__(*commands, prefixes=prefixes, strict=strict)

        with open(self.get_path("data"), "r") as o:
            self.data = json.load(o)
        self.max_chars = max_chars
        self.smiles = smiles

        self.description = [f"Выводит текст с помощью Emoji.",
                            f"{self.command_example()} текст - выводит текст с помосщью emoji"]

    async def process_message(self, msg):
        command, text = self.parse_message(msg)

        prepare = text.upper()

        if len(prepare) > self.max_chars:
            return await msg.answer(f"Не более {self.max_chars} символов!")

        resultm = ""
        for c in prepare:
            temp = ""
            for i in range(9):
                temp += self.data[c][i].replace("1", self.smiles[0]).replace("0", self.smiles[1]) + "\n"

            if len(resultm + temp) > 4000:
                await msg.answer(resultm)
                resultm = temp
            else:
                resultm += temp

        if resultm:
            await msg.answer(resultm)
