import traceback

import hues
import re

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

        if not cmd.good_cmd:
            return False

        if self.convert:
            translated_cmd_text = convert_to_rus(cmd.joined_text)
        else:
            translated_cmd_text = ''

        for command in self.commands:
            command = command.lower()
            if command in cmd.
            try:
                await self.system.call_command(command, msg_obj, cmd.args)
                return True
            # Если в плагине какая-то ошибка
            except Exception:
                await msg_obj.answer("{}.".format(msg_obj.vk.anti_flood()) +
                                     "Произошла ошибка при выполнении команды <{}>, ".format(command) +
                                     "пожалуйста, сообщите об этом разработчику!")
                hues.error(
                    "Произошла ошибка при вызове команды '{cmd}'. "
                    "Сообщение: '{body}' с параметрами {args}. "
                    "Ошибка:\n{traceback}".format(
                        cmd=command, body=msg_obj._data, args=cmd.args,
                        traceback=traceback.format_exc()
                    ))
            break


class Command(object):
    __slots__ = ('good_cmd', '_data', 'text', 'joined_text',
                 'command', 'args', 'try_convert', 'eng_layout')

    def __init__(self, data: MessageEventData, convert: bool):
        self.good_cmd = True  # переменная для обозначения, всё ли хорошо с командой
        self._data = data
        self.text = data.body
        self.try_convert = convert
        self.joined_text = ''.join(self.text).lower()  # команда без пробелов в нижнем регистре
        self.command = None
        self.__get_prefix()  # Узнаём свой префикс

    def set(self, command: str, convert: bool = False):
        self.eng_layout = True if convert else self.eng_layout
        self.command = command
        if self.eng_layout:
            self.text = re.sub(re.escape(convert_to_rus(command)), '',
                               self.text, flags=re.IGNORECASE)
        else:
            self.text = re.sub(re.escape(command), '', self.text, flags=re.IGNORECASE)
        if self.good_cmd:
            self.__get_args()  # Получаем свои аргументы
            self.log()

    def log(self):
        cid = self._data.peer_id
        who = ("конференции {}" if self._data.conf else "ЛС {}").format(cid)
        hues.info("Команда '{cmd}' из {who} с аргументами {args}.".format(
            cmd=self.command, who=who, args=self.args
        ))

    def __get_prefix(self):
        for prefix in PREFIXES:
            self.eng_layout = False
            if self.text.startswith(prefix):
                self.text = self.text.replace(prefix, '', 1).lstrip()
                break
            elif self.try_convert:
                # Префикс, написанный русскими буквами, но на английской раскладке
                prefix_en = convert_to_en(prefix)
                if self.text.startswith(prefix_en):
                    self.eng_layout = True
                    self.text = self.text.replace(prefix_en, '', 1).lstrip()
                    break
        else:
            self.good_cmd = False

    def __get_args(self):
        self.args = self.text.split()
