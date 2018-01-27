from handler.base_plugin import BasePlugin
from random import choice, shuffle

import json


class AnagramsPlugin(BasePlugin):
    __slots__ = ("save_data", "commands_start", "commands_stop", "commands_attempt",
                 "prefixes", "words", "games")

    def __init__(self, commands_start=None, commands_stop=None, commands_attempt=None,
                 prefixes=(), words=None, save_data=False):
        """Game "Anagrams"."""

        super().__init__()

        self.save_data = save_data
        self.prefixes = prefixes

        self.commands_start = commands_start if commands_start else ["анаграмма", "анаграммы"]
        self.commands_attempt = commands_attempt if commands_attempt else ["ответ", "о"]
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
            self.bot.logger.error("Failed to load games for \"Anagram\"")

        except FileNotFoundError:
            pass

        for c in (self.commands_start, self.commands_attempt, self.commands_stop):
            c = sorted(c, key=len, reverse=True)

        self.description = [f"Анаграммы",
                            f"Игра \"Анаграммы\" - игроки вводят слова и стараются угадать слово.",
                            f"{self.prefixes[0]}{self.commands_start[0]} - начать игру.",
                            f"{self.prefixes[0]}{self.commands_attempt[0]} [слово] - назвать слово [слово].",
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
                    msg.meta["_word"] = check_text[len(v) + 1:]
                    return True

        return False

    def describe_game(self, current):
        text = ["👽 Анаграмма: ", current[0], "\n", self.prefixes[0] + self.commands_attempt[0],
                " - назвать слово.\n", self.prefixes[0] + self.commands_stop[0], " - сдаться."]

        return " ".join(text)

    async def global_before_message_checks(self, msg):
        if self.games.get(msg.peer_id, False) is False:
            return

        msg.occupied_by.append(self)

        return

    # word, anagram
    async def process_message(self, msg):
        if msg.meta["_command"] == "stop":
            current = self.games.get(msg.peer_id, [])
            if current:
                del self.games[msg.peer_id]

                return await msg.answer("Ваша партия в \"анаграммы\" закончена. Слово я вам не назову 😏")

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

            oword = choice(self.words)
            word = list(oword)

            shuffle(word)
            word = "".join(word)

            self.games[msg.peer_id] = [word, oword]

            return await msg.answer(self.describe_game(self.games[msg.peer_id]))

        if msg.meta["_command"] == "attempt":
            current = self.games.get(msg.peer_id, [])

            if not current:
                return

            word = msg.meta.get("_word", "")

            if not word:
                return await msg.answer("Введите только одну букву!")

            if word.lower().strip() != current[1].lower().strip():
                return await msg.answer("Не верно!\n" + self.describe_game(current))

            if msg.peer_id in self.games:
                del self.games[msg.peer_id]

            return await msg.answer(f"🎉 Верно! Ура\n👉 Слово: " + current[1])
