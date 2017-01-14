import traceback

import hues
import re

from utils import convert_to_rus, convert_to_en
from settings import PREFIXES


class CommandSystem(object):
    def __init__(self, commands, plugin_system, convert_layout=True):
        # Система плагинов
        self.system = plugin_system
        # self.commands - список с командами
        self.commands = commands
        # Конвертировать ли команду в русскую раскладку?
        self.convert = convert_layout

    async def process_command(self, msg_obj):
        """Обработать объект Message"""
        # Создаём объект cmd
        cmd = Command(msg_obj._values)

        if not cmd.good_cmd:
            return

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
            # Если в плагине какая-то ошибка
            except Exception:
                await msg_obj.answer("{}.".format(msg_obj.vk.anti_flood()) +
                                     "Произошла ошибка при выполнении команды <{}>, ".format(command) +
                                     "пожалуйста, сообщите об этом разработчику!")
                hues.error(
                    "Произошла ошибка при вызове команды '{cmd}'. "
                    "Сообщение: '{body}' с параметрами {args}. "
                    "Ошибка:\n{traceback}".format(
                        cmd=command, body=msg_obj._values, args=cmd.args,
                        traceback=traceback.format_exc()
                    ))
            break


class Command(object):
    def __init__(self, answer: dict):
        self.good_cmd = True  # переменная для обозначения, всё ли хорошо с командой
        self.values = answer
        self.text = answer['body']
        self.__get_prefix()  # Узнаём свой префикс
        self.joined_text = ''.join(self.text).lower()  # команда без пробелов в нижнем регистре

    def set(self, command: str, convert=False):
        self.command = command
        if convert:
            self.text = re.sub(re.escape(convert_to_en(command)), '', self.text, flags=re.IGNORECASE)
            # self.text = self.text.replace(convert_to_en(command), '')
        else:
            self.text = re.sub(re.escape(command), '', self.text, flags=re.IGNORECASE)
            # self.text = self.text.replace(self.command, '')
        if self.good_cmd:
            self.__get_args()  # Получаем свои аргументы
            self.log()

    def log(self):
        conversation_id = str(self.values.get('user_id', self.values.get('chat_id')))
        if 'user_id' in self.values:
            conversation_id = 'ЛС от http://vk.com/id' + conversation_id
        else:
            conversation_id = "конференции" + conversation_id
        hues.info("Команда '{cmd}' из ({cid}) с аргументами {args}.".format(
            cmd=self.command, cid=conversation_id, args=self.args
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
