from handler.base_plugin_command import CommandPlugin

import datetime


class TimePlugin(CommandPlugin):
    __slots__ = ("delta", "message", "days")

    def __init__(self, *commands, prefixes=None, strict=False, offseth=3, offsetm=0, message=None):
        """Answers with current date and time."""

        super().__init__(*commands, prefixes=prefixes, strict=strict)

        self.message = message or "Текущие дата и время по МСК:"
        self.delta = datetime.timedelta(hours=offseth, minutes=offsetm)
        self.days = {0: 'понедельник', 1: 'вторник', 2: 'среда', 3: 'четверг',
                     4: 'пятница', 5: 'суббота', 6: 'воскресенье'}

        example = self.command_example()
        self.description = [f"Текущее время",
                            f"{example} - показывает текущее время и дату."]

    async def process_message(self, msg):
        time = (datetime.datetime.now(datetime.timezone.utc) + self.delta)
        timestr = time.strftime('%d-%m-%Y %H:%M:%S')

        await msg.answer(f'{self.message}\n{timestr}\nСегодня {self.days[time.weekday()]}')
