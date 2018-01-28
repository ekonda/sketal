from handler.base_plugin_command import CommandPlugin
from plugins.content.calculation.calculator import Calculator

class CalculatorPlugin(CommandPlugin):
    __slots__ = ("calculator", )

    def __init__(self, *commands, prefixes=None, strict=False):
        """Calculator plugin"""

        super().__init__(*commands, prefixes=prefixes, strict=strict)

        self.calculator = Calculator()

        example = self.command_example()
        self.description =[f"Калькулятор",
                           f"{example} [выражение] - посчитать выражение."]

    async def process_message(self, msg):
        command, text = self.parse_message(msg)

        success, result = self.calculator.calculate_safe(text, **self.calculator.default_variables)

        if success:
            return await msg.answer("Результат: " + str(result))

        return await msg.answer("Ошибка в выражении")
