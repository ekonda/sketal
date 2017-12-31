from handler.base_plugin import BasePlugin


class CommandPlugin(BasePlugin):
    __slots__ = ("commands", "strict", "prefixes")

    def __init__(self, *commands, prefixes=None, strict=False):
        super().__init__()

        self.commands = commands if strict else [command.strip().lower() for command in commands]
        self.commands = sorted(self.commands, key=lambda x: len(x), reverse=True)  # или x.count(" ")?

        self.prefixes = prefixes if prefixes else ("!", )
        self.prefixes = sorted(self.prefixes, reverse=True)

        self.strict = strict

    def command_example(self, command_index=0):
        return f"{self.prefixes[-1] if self.prefixes else ''}{self.commands[command_index]}"

    def get_checking_text(self, msg):
        if self.strict:
            return msg.full_text

        else:
            return msg.text

    def parse_message(self, msg, full_text=None):
        """ Returns message without command from Message object"""

        text = self.get_checking_text(msg) if full_text is None else (msg.full_text if full_text else msg.text)

        if "__command__" in msg.data and "__prefix__" in msg.data:
            command = msg.data["__command__"]

            return command, text[len(msg.data["__prefix__"]) + len(command):].strip(" ")

        return self.parse_text(text)

    def parse_text(self, text):
        """ Returns message without command from string"""

        for v in self.prefixes:
            if text.startswith(v):
                text = text.replace(v, "", 1)
                break

        for command in self.commands:
            if text.startswith(command + " ") or text.startswith(command + "\n") or text == command:
                return command, text[len(command):].strip(" ")

        return "", text.strip()

    async def check_message(self, msg):
        text = self.get_checking_text(msg)

        for v in self.prefixes:
            if text.startswith(v):
                msg.data["__prefix__"] = v

                text = text.replace(v, "", 1)

                if text and text[0] == " ": text = text[1:]

                break

        else:
            return False

        for command in self.commands:
            if text.startswith(command + " ") or text.startswith(command + "\n") or text == command:
                msg.data["__command__"] = command

                return True

        return False

    async def process_message(self, msg):
        await msg.answer("Команда: (" + ", ".join(self.commands) + ")")
