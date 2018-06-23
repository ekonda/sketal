from handler.base_plugin import CommandPlugin


class AboutPlugin(CommandPlugin):
    __slots__ = ("version", )

    def __init__(self, *commands, prefixes=None, strict=False, version=8.0):
        """Answers with information about bot."""

        if not commands:
            commands= ("о боте",)

        super().__init__(*commands, prefixes=prefixes, strict=strict)

        self.version = version

        self.description = (
            "О боте",
            "Вывод информации о боте.",
            f"{self.command_example()} - вывести информацию."
        )

    async def process_message(self, msg):
        message = "🌍 sketal 🌍\n" \
                  "🌲 sketal - бот, способный выполнять очень сложные задачи, команды. На основе этого бота " \
                  "можно строить очень сложные системы и сервисы. Этот бот очень надёжен и стабилен - обрабатывает " \
                  "очень многие ошибки и избегает их. Бот обновляется, обретает новые плагины и т.д.\n" \
                  "🌲 Версия: " + str(self.version) + "\n" \
                  "🌲 https://github.com/vk-brain/sketal\n" \
                  "🌲 http://michaelkrukov.ru/\n"

        return await msg.answer(message)
