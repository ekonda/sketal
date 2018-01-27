from handler.base_plugin_command import CommandPlugin


class xPlugin(CommandPlugin):
    __slots__ = ()

    def __init__(self, *commands, prefixes=None, strict=False):
        super().__init__(*commands, prefixes=prefixes, strict=strict)

    async def process_message(self, msg):
        command, text = self.parse_message(msg)
