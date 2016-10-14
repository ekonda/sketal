from threading import Thread

from settings import prefixes
import hues


class CommandSystem(object):
    def __init__(self, commands, plugin_system):
        self.system = plugin_system
        # Получаем команды без пробелов
        # Получаем словарь 'команда_без_пробелов' -> 'команда с пробелами'
        self.commands = commands

    async def process_command(self, answer: dict, vk_object):

        cmd = Command(answer)

        if not cmd.good_cmd:
            return

        for command in self.commands:
            if not cmd.joined_text.startswith(''.join(command)):
                continue  # Если сообщение не начинается с команды, берём след. элемент

            cmd.set(command)
            # t = Thread(target=
            await self.system.call_command(command, vk_object, answer,
                                           cmd.args)  # , args=(command, vk_object, answer, cmd.args))
            # t.start()
            break


class Command(object):
    def __init__(self, answer):
        self.good_cmd = True  # переменная для обозначения, всё ли хорошо с командой
        self.values = answer
        if not answer['body']:
            return
        self.text = answer['body']
        self.__get_prefix()  # Узнаём свой префикс
        self.joined_text = ''.join(self.text).lower()  # команда без пробелов в нижнем регистре

    def set(self, command):
        self.command = command
        self.text = self.text.replace(self.command, '')
        if self.good_cmd:
            self.__get_args()  # Получаем свои аргументы
            self.log()

    def log(self):
        if 'chat_id' in self.values:
            chat_id = self.values['chat_id']
            hues.info("Команда '{cmd}' из конференции ({cid}) с аргументами {args}.".format(
                cmd=self.command, cid=chat_id, args=self.args
            ))
        elif 'user_id' in self.values:
            user_id = self.values['user_id']
            hues.info("Команда '{cmd}' из ЛС (http://vk.com/id{uid}) с аргументами {args}.".format(
                cmd=self.command, uid=user_id, args=self.args
            ))

    def __get_prefix(self):
        for prefix in prefixes:
            if self.text.startswith(prefix):
                self.prefix = prefix
                self.text = self.text.replace(prefix, '')
                break
        else:
            self.good_cmd = False

    def __get_args(self):
        self.args = self.text.split()
