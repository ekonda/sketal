from handler.base_plugin_command import CommandPlugin


class HelpPlugin(CommandPlugin):
    __slots__ = ("plugins", "short")

    def __init__(self, *commands, plugins=None, short=True, prefixes=None, strict=False):
        """Answers with a user a list with plugins's descriptions from `plugins`."""

        super().__init__(*commands, prefixes=prefixes, strict=strict)

        self.short = short

        if not isinstance(plugins, list):
            self.plugins = []

        else:
            self.plugins = plugins

        self.set_description()

    def set_description(self):
        example = self.command_example()
        self.description = ["Список доступных команд",
                            "Вывод списка доступных команд.",
                            f"{example} - показать список."]

    def add_plugins(self, plugins):
        for plugin in plugins:
            if plugin not in self.plugins:
                self.plugins.append(plugin)

    def set_plugins(self, plugins):
        if not isinstance(plugins, (list, tuple)):
            return

        self.plugins = plugins

    async def process_message(self, msg):
        result = ""

        for plugin in self.plugins:
            if not hasattr(plugin, "description") or not plugin.description:
                continue

            if self.short:
                result += "🔶 " + plugin.description[0] + ". " + " // ".join(plugin.description[1:]) + "\n"
                continue

            result += "🔷" + plugin.description[0] + ":🔷" + "\n"
            result += "🔶 " + "\n🔶 ".join(plugin.description[1:]) + "\n"
            result += "\n"

        await msg.answer(result.strip())
