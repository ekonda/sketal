import traceback

import hues
import settings
from plugin_system import PluginSystem
from utils import convert_to_rus, convert_to_en, MessageEventData
from settings import PREFIXES
from vkplus import Message


class CommandSystem(object):
    def __init__(self, commands, plugin_system: PluginSystem, convert_layout=True):
        # Система плагинов
        self.system = plugin_system
        # self.commands - список с командами
        self.commands = commands
        # Конвертировать ли команду в русскую раскладку?
        self.convert = convert_layout

    async def process_command(self, msg_obj: Message):
        """Обработать объект Message"""
        cmd = Command(msg_obj._data, self.convert)

        if not cmd.has_prefix:
            return False
        # Если команда есть в списке команд
        if cmd.command in self.commands:
            command = cmd.command
        # Или нужно попробовать конвертировать и изменённая команда в командах
        elif self.convert and cmd.try_convert() in self.commands:
            cmd.convert()
            command = cmd.command
        else:
            return False
        # Логгируем команду, если нужно
        if settings.LOG_COMMANDS:
            cmd.log()
        try:
            await self.system.call_command(command, msg_obj, cmd.args)
            return True
        # Если в плагине произошла какая-то ошибка
        except Exception:
            await msg_obj.answer("{}.".format(msg_obj.vk.anti_flood()) +
                                 "Произошла ошибка при выполнении команды <{}>, ".format(command) +
                                 "пожалуйста, сообщите об этом разработчику!")
            hues.error(
                "Произошла ошибка при вызове команды '{cmd}' с аргументами {args}"
                "Текст сообщения: '{body}'."
                "Ошибка:\n{tbk}".format(
                    cmd=command, body=msg_obj._data, args=cmd.args,
                    tbk=traceback.format_exc()
                ))


class Command(object):
    __slots__ = ('has_prefix', '_data', 'text',
                 'command', 'args', 'need_convert')

    def __init__(self, data: MessageEventData, convert: bool):
        self.has_prefix = True  # переменная для обозначения, всё ли хорошо с командой
        self._data = data
        self.text = data.body
        self.need_convert = convert
        self._get_prefix()  # Узнаём свой префикс
        self.command, *self.args = self.text.split(' ')
        # Если команда пустая
        if not self.command.strip():
            self.has_prefix = False

    def try_convert(self):
        return convert_to_rus(self.command)

    def convert(self):
        self.command = convert_to_rus(self.command)
        self.args = [convert_to_rus(arg) for arg in self.args]

    def log(self):
        pid = self._data.peer_id
        who = ("конференции {}" if self._data.conf else "ЛС {}").format(pid)
        hues.info("Команда '{cmd}' из {who} с аргументами {args}.".format(
            cmd=self.command, who=who, args=self.args
        ))

    def _get_prefix(self):
        # Проходимся по всем префиксам
        for prefix in PREFIXES:
            # Если команда начинается с префикса
            if self.text.startswith(prefix):
                # Убираем префикс из текста
                self.text = self.text.replace(prefix, '', 1).lstrip()
                break
            elif self.need_convert:
                # Префикс, написанный русскими буквами, но на английской раскладке
                prefix_en = convert_to_en(prefix)
                # Если команда начинается с префикса в английской раскладке
                if self.text.startswith(prefix_en):
                    # Убираем префикс из текста
                    self.text = self.text.replace(prefix_en, '', 1).lstrip()
                    break
        else:
            self.has_prefix = False
