from handler.base_plugin import BasePlugin
from random import choice

import json


class HangmanPlugin(BasePlugin):
    __slots__ = ("commands_start", "save_data", "commands_stop", "commands_attempt", "prefixes", "games",
                 "words")

    def __init__(self, commands_start=None, commands_stop=None, commands_attempt=None,
            prefixes=(), words=None, save_data=False):
        """Game "Hangman"."""

        super().__init__()

        self.save_data = save_data
        self.prefixes = prefixes
        self.commands_start = commands_start if commands_start else ["виселица"]
        self.commands_attempt = commands_attempt if commands_attempt else ["буква", "б"]
        self.commands_stop = commands_stop if commands_stop else ["стоп"]
        self.games = {}

        self.words = words if words else ("любовь", "ненависть", "страсть", "жизнь", "счастье", "крот", "бегемот")

        games_file = self.get_path("games.json")

        try:
            with open(games_file, "r") as outfile:
                data = json.load(outfile)

                for k, v in data.items():
                    self.games[int(k)] = v

        except json.decoder.JSONDecodeError:
            self.bot.logger.error("Failed to load games for \"Hangman\"")

        except FileNotFoundError:
            pass

        for c in (self.commands_start, self.commands_attempt, self.commands_stop):
            c = sorted(c, key=len, reverse=True)

        self.description = [f"Виселица",
                            f"Игра \"Виселица\" - игроки вводят по букве и стараются угадать слово."
                            "Если не получится отгадать за 8 попыток - вы проиграете!",
                            f"{self.prefixes[0]}{self.commands_start[0]} - начать игру.",
                            f"{self.prefixes[0]}{self.commands_attempt[0]} [буква] - назвать букву [буква].",
                            f"{self.prefixes[0]}{self.commands_stop[0]} - остановить игру."]

    def stop(self):
        if not self.save_data:
            return

        games_file = self.get_path("games.json")

        with open(games_file, "w") as outfile:
            json.dump(self.games, outfile)

    async def check_message(self, msg):
        if msg.is_out:
            return False

        check_text = ""
        for p in self.prefixes:
            if msg.text.startswith(p):
                check_text = msg.text.replace(p, "", 1)
                break

        if any(check_text.startswith(v.lower()) for v in self.commands_start):
            msg.meta["_command"] = "start"
            return True

        if self in msg.occupied_by and any(check_text.startswith(v.lower()) for v in self.commands_stop):
            msg.meta["_command"] = "stop"
            return True

        if self in msg.occupied_by:
            for v in self.commands_attempt:
                if check_text.startswith(v + " "):
                    msg.meta["_command"] = "attempt"
                    msg.meta["_letter"] = check_text[len(v) + 1:]
                    return True

        return False

    @staticmethod
    def describe_game(current):
        text = ["🙊 Слово: "]

        for i in current[0]:
            text.append(i if i in current[1] else "_")
            text.append(" ")

        text.pop(-1)

        text.append("\n🙌 Открытые буквы: ")

        for i in current[1]:
            if i in current[0]:
                text.append(i)
                text.append(" ")

        text.pop(-1)

        text.append(f"\n❤ Осталось жизней: {current[2]}")

        return " ".join(text)

    async def global_before_message_checks(self, msg):
        if self.games.get(msg.peer_id, False) is False:
            return

        msg.occupied_by.append(self)

        return

    # word, opened, lives
    async def process_message(self, msg):
        if msg.meta["_command"] == "stop":
            current = self.games.get(msg.peer_id, [])

            if current:
                del self.games[msg.peer_id]

                return await msg.answer("Ваша партия в \"виселицу\" закончена. Слово я вам не назову 😏")

            return

        if msg.meta["_command"] == "start":
            current = self.games.get(msg.peer_id, [])

            if current:
                return await msg.answer(self.describe_game(self.games[msg.peer_id]))

            if msg.occupied_by:
                try:
                    reason = " Вы заняты плагином: " + msg.occupied_by[0].description[0]
                except (AttributeError, IndexError):
                    reason = ""

                return await msg.answer("Вы не можете сейчас начать игру!" + reason )

            self.games[msg.peer_id] = [choice(self.words), "", 8]

            tip = f"\n\n{self.prefixes[0]}{self.commands_attempt[0]} - назвать букву, " \
                  f"{self.prefixes[0]}{self.commands_stop[0]} - остановить игру"

            return await msg.answer(self.describe_game(self.games[msg.peer_id]) + tip)

        if msg.meta["_command"] == "attempt":
            current = self.games.get(msg.peer_id, [])

            if not current:
                return

            letter = msg.meta.get("_letter", "")

            if len(letter) != 1 or not letter.isalpha():
                return await msg.answer("Введите только одну букву!")

            if letter in current[1]:
                return await msg.answer("Вы уже вводили эту букву!")

            current[1] += letter

            if letter not in current[0]:
                if current[2] == 1:
                    if msg.peer_id in self.games:
                        del self.games[msg.peer_id]

                    return await msg.answer("Вы проиграли! Слово я вам не назову 😏")

                current[2] -= 1

                return await msg.answer(f"Вы не угадали! У вас осталось {current[2]} жизней.\n"+
                                        self.describe_game(self.games[msg.peer_id]))

            for i in current[0]:
                if i not in current[1]:
                    return await msg.answer(f"Верно! Продолжайте в том же духе!\n" +
                                            self.describe_game(self.games[msg.peer_id]))

            if msg.peer_id in self.games:
                del self.games[msg.peer_id]

            return await msg.answer(f"🎉 Верно! Ура\n👉 Слово: " + current[0])
