from handler.base_plugin import BasePlugin

import re


class CommandPlugin(BasePlugin):
    __slots__ = ("commands", "strict", "prefixes")

    def __init__(self, *commands, prefixes=None, strict=False):
        super().__init__()

        self.commands = commands if strict else [command.strip().lower() for command in commands]
        self.commands = sorted(self.commands, key=len, reverse=True)  # или x.count(" ")?

        self.prefixes = prefixes if prefixes else ("!", )
        self.prefixes = sorted(self.prefixes, reverse=True)

        self.strict = strict

    def command_example(self, command_index=0):
        return f"{self.prefixes[-1] if self.prefixes else ''}{self.commands[command_index]}"

    @staticmethod
    def parse_message(msg, full_text=None):
        """ Returns message without command from Message object"""

        return msg.meta["__command"], msg.meta["__arguments_full"] if full_text else msg.meta["__arguments"]

    async def check_message(self, msg):
        subtext = ""
        subtext_full = ""

        for v in self.prefixes:
            if msg.text.startswith(v):
                msg.meta["__prefix"] = v

                subtext = msg.text[len(v):].strip()
                subtext_full = msg.full_text[len(v):].strip()

                break

        else:
            return False

        for command in self.commands:
            if self.strict:
                match = re.search(rf"^{re.escape(command)}( +|\n+|$)", subtext_full)
            else:
                match = re.search(rf"^{re.escape(command)}( +|\n+|$)", subtext)

            if match:
                msg.meta["__command"] = command

                msg.meta["__arguments"] = subtext[match.end():].strip()
                msg.meta["__arguments_full"] = subtext_full[match.end():].strip()

                return True

        return False

    async def process_message(self, msg):
        await msg.answer("Команда: (" + ", ".join(self.commands) + ")")
