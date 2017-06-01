import traceback

import hues

from plugin_system import PluginSystem
from vkplus import Message

try:
    import settings
except ImportError:
    pass


class Command(object):
    __slots__ = ('has_prefix', 'text', 'bot',
                 'command', 'args', "msg")

    def __init__(self, msg: Message):
        self.has_prefix = True  # переменная для обозначения, есть ли у команды префикс
        self.msg = msg
        self.text = msg.body
        self._get_prefix()
        self.command = ""
        self.args = []
        # Если команда пустая
        if not self.text.strip():
            self.has_prefix = False

    def check_command(self, command_system):
        if not self.has_prefix:
            return False

        for command in command_system.commands:
            if self.text.startswith(command + " ") or self.text == command:
                self.command = command
                self.args = self.text.replace(command, "", 1).split()
                self.msg.text = " ".join(self.args)
                return True

        if command_system.ANY_COMMANDS:
            self.args = self.text.split()
            self.msg.text = " ".join(self.args)
            return True

        return False

    def log(self):
        """Пишет в лог, что была распознана команда"""
        pid = self.msg.peer_id
        who = ("конференции {}" if self.msg.conf else "ЛС {}").format(pid)
        hues.info(f"Команда '{self.command}' из {who} с аргументами {self.args}")

    def _get_prefix(self):
        """Пытается получить префикс из текста команды"""
        for prefix in settings.PREFIXES:
            # Если команда начинается с префикса
            if self.text.startswith(prefix):
                # Убираем префикс из текста
                self.text = self.text.replace(prefix, '', 1).lstrip()
                self.msg.text = self.text
                break

        else:
            self.has_prefix = False


class CommandSystem(object):
    def __init__(self, commands, plugin_system: PluginSystem):
        # Система плагинов
        self.system = plugin_system
        # self.commands - список с командами
        self.commands = commands
        self.ANY_COMMANDS = bool(plugin_system.any_commands)

    async def process_command(self, msg_obj: Message, cmd: Command):
        """Обрабатывает команду"""
        if not cmd.check_command(self):
            return False

        cmd_text = cmd.command
        # Логгируем команду, если нужно (но не логгируем плагины,
        # которые реагируют на любые команды)
        if settings.LOG_COMMANDS and not self.ANY_COMMANDS:
            cmd.log()
        try:
            await self.system.call_command(cmd_text, msg_obj, cmd.args)

            return True
        # Если в плагине произошла какая-то ошибка
        except Exception:
            await msg_obj.answer(f"{msg_obj.vk.anti_flood()}. "
                                 f"Произошла ошибка при выполнении команды <{cmd_text}> "
                                 "пожалуйста, сообщите об этом разработчику!")
            hues.error(
                f"Произошла ошибка при вызове команды '{cmd_text}' с аргументами {cmd.args}. "
                f"Текст сообщения: '{msg_obj._data}'."
                f"Ошибка:\n{traceback.format_exc()}")
