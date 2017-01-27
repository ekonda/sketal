import traceback

import hues
import re

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
        # Создаём объект cmd
        cmd = Command(msg_obj._data)

        if not cmd.good_cmd:
            return False

        if self.convert:
            translated_cmd_text = convert_to_rus(cmd.joined_text)
        else:
            translated_cmd_text = ''
        for command in self.commands:
            # cmd_text - команда без пробелов
            cmd_text = ''.join(command)
            # Если текст - команда
            if cmd.joined_text.startswith(cmd_text):
                cmd.set(command)
            # Если текст, переведённый на русскую раскладку - команда
            elif translated_cmd_text.startswith(cmd_text):
                cmd.set(command, convert=True)
            else:  # Если сообщение не начинается с команды, берём след. элемент
                continue
            # Вызываем команду в плагинах
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
    __slots__ = ('good_cmd', '_data', 'text', 'joined_text', 'command',
                 'prefix', 'args')

    def __init__(self, data: MessageEventData):
        self.good_cmd = True  # переменная для обозначения, всё ли хорошо с командой
        self._data = data
        self.text = data.body
        self.__get_prefix()  # Узнаём свой префикс
        self.joined_text = ''.join(self.text).lower()  # команда без пробелов в нижнем регистре
        self.command = None

    def set(self, command: str, convert: bool = False):
        self.command = command
        if convert:
            self.text = re.sub(re.escape(convert_to_en(command)), '',
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
            if self.text.startswith(prefix):
                self.prefix = prefix
                self.text = self.text.replace(prefix, '', 1).lstrip()
                break
        else:
            self.good_cmd = False

    def __get_args(self):
        self.args = self.text.split()
