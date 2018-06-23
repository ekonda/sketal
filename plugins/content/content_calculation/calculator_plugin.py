from handler.base_plugin import CommandPlugin
from .calculator import Calculator

class CalculatorPlugin(CommandPlugin):
    __slots__ = ("calculator", )

    def __init__(self, *commands, prefixes=None, strict=False):
        "Calculator plugin"

        if not commands:
            commands = ("посчитай",)

        super().__init__(*commands, prefixes=prefixes, strict=strict)

        self.calculator = Calculator()

        example = self.command_example()
        self.description =[f"Калькулятор",
                           f"{example} [выражение] - посчитать выражение."]

    async def process_message(self, msg):
        command, text = self.parse_message(msg)

        success, result = self.calculator.calculate_safe(text)

        if success:
            return await msg.answer("Результат: " + str(result))

        return await msg.answer("Ошибка в выражении")
