from handler.base_plugin_command import CommandPlugin
from vk_special_methods import parse_user_id
from utils import plural_form

import asyncio, re

# Requirements:
#
# ChatMetaPlugin

class VoterPlugin(CommandPlugin):
    __slots__ = ("command_groups", "votes")

    def __init__(self, vote_commands=None,  vote_undo_commands=None, votekick_commands=None, prefixes=None, strict=False):
        if not vote_commands:
            vote_commands = ["vote", "+"]

        if not vote_undo_commands:
            vote_undo_commands = ["unvote", "-"]

        if not votekick_commands:
            votekick_commands = ["votekick", "выгоняем"]

        super().__init__(*(vote_commands + votekick_commands + vote_undo_commands), prefixes=prefixes, strict=strict)

        self.command_groups = vote_commands, vote_undo_commands, votekick_commands
        self.votes = {}

    async def do_vote(self, msg, title, maximum=None, votetime=180, kick=None):
        maximum = min(len(msg.meta["__chat_data"].users), maximum if maximum else float("inf"))
        await msg.answer(
            f"Начало голосование с темой \"{title}\". Максимальное кол-во проголосовавших: {maximum}. "
            f"Время голосования: {round(votetime/60, 2)} мин. Голосовать - {self.prefixes[-1]}{self.command_groups[0][0]}"
        )

        async def tick(timeleft):
            await msg.answer(f"До конца голосования {plural_form(timeleft, ('секунда', 'секунды', 'секунд'))} ({len(self.votes[msg.chat_id])}/{maximum}).")

        if votetime == 180:
            times = [60, 60, 30, 15, 10, 5]
        else:
            times = []

            temp = votetime
            while temp > 0:
                step = min(60, temp // 2)

                while step % 5 != 0 and step < temp:
                    step += 1

                times.append(step)
                temp -= step

        await tick(votetime)
        for delta in times:
            await asyncio.sleep(delta)
            votetime -= delta
            if votetime > 0: await tick(votetime)

        result = len(self.votes[msg.chat_id])

        if result >= maximum:
            text = f"Голосование закончено c положительным результатом"
        else:
            text = "Голосование закончено с негативным результатом"
        text += f" ({result}/{maximum})!"

        await msg.answer(text)

        if kick and result >= maximum:
            await self.api.messages.removeChatUser(chat_id=msg.chat_id, user_id=kick)

        del self.votes[msg.chat_id]

    async def process_message(self, msg):
        if msg.chat_id == 0:
            return await msg.answer("Эта команда доступна только в беседах.")

        if "__chat_data" not in msg.meta:
            raise ValueError("This plugin requires `ChatMetaPlugin`.")

        command, text = self.parse_message(msg, True)

        if command in self.command_groups[0]:
            if msg.chat_id not in self.votes:
                if text:
                    match = re.match(r"\((\d+?)(, ?\d+?)?\)", text)
                    if match:
                        maximum = int(match.group(1)) if match.group(1) else None
                        votetime = int(match.group(2)[1:].strip()) if match.group(2) else 180
                        title = text[match.end():].strip()
                    else:
                        maximum = None
                        votetime = 180
                        title = text.strip()

                    self.votes[msg.chat_id] = set()

                    return asyncio.ensure_future(self.do_vote(msg, title, maximum=maximum, votetime=votetime))

                return await msg.answer("Голосованй не идёт в данный момент.")

            if text:
                return await msg.answer("Голосование уже идёт. Подождите его завершения.")

            if msg.user_id in self.votes[msg.chat_id]:
                return await msg.answer("Вы уже голосовали.")

            self.votes[msg.chat_id].add(msg.user_id)

            return await msg.answer("ОК+")

        if command in self.command_groups[1]:
            if msg.chat_id not in self.votes:
                return await msg.answer("Голосованй не идёт в данный момент.")

            if msg.user_id not in self.votes[msg.chat_id]:
                return await msg.answer("Вы не голосовали.")

            self.votes[msg.chat_id].remove(msg.user_id)

            return await msg.answer("ОК-")

        if command in self.command_groups[2]:
            if msg.chat_id in self.votes:
                return await msg.answer("Голосование уже идёт. Подождите его завершения.")

            puid = await parse_user_id(msg)

            if not puid:
                return await msg.answer(
                    "Введите пользователя, которого хотите выкинуть голосованием.\nПример: " +
                    self.prefixes[0] + self.command_groups[2][0] + " 87641997"
                )

            user = None
            for u in msg.meta["__chat_data"].users:
                if u["id"] == puid:
                    user = u
                    break

            if not user:
                return await msg.answer("Вы пытаетесь выгнать пользователя, которого нет в беседе.")

            self.votes[msg.chat_id] = set()

            return asyncio.ensure_future(self.do_vote(msg, f"Кик пользователя: {user['first_name']} {user['last_name']}", 10, kick=puid))
