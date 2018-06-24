from handler.base_plugin import CommandPlugin
from utils import parse_user_id

import random


class TicTacToePlugin(CommandPlugin):
    __slots__ = (
        "c_invite", "c_decline", "c_accept", "c_make_turn",
        "invites", "games", "game_name"
    )

    def __init__(self, c_invite=None, c_decline=None, c_accept=None,
            c_make_turn=None, prefixes=None, strict=False):
        if not c_invite:
            c_invite = ("кн вызов",)

        if not c_decline:
            c_decline = ("кн тказаться",)

        if not c_accept:
            c_accept = ("кн принять",)

        if not c_make_turn:
            c_make_turn = ("кн ход",)

        super().__init__(*(c_invite + c_decline + c_accept + c_make_turn), prefixes=prefixes, strict=strict)

        self.c_invite = c_invite
        self.c_decline = c_decline
        self.c_accept = c_accept
        self.c_make_turn = c_make_turn

        self.game_name = "Крестики и нолики"

        self.invites = {}
        self.games = {}

    def game(self, game, controls=True):
        message = \
            f"💭 Текущее поле:\n" + \
            "\n".join(" ".join(line) for line in game["field"])

        if controls:
            message += \
                f"\n👉 Напишите {self.prefixes[-1]}{self.c_make_turn[0]} слобик_клетки строка_клетки - чтобы сходить туда.\n" + \
                f"👉 Напишите {self.prefixes[-1]}{self.c_make_turn[0]} сдаться - чтобы сдаться."

        return message

    async def process_message(self, msg):
        command, text = self.parse_message(msg)

        if command in self.c_invite:
            puid = await parse_user_id(msg)

            if not puid:
                return await msg.answer("🤜🏻 Вы не указали, кого вызывать!")

            if puid in self.games:
                return await msg.answer("🤜🏻 Этот человек уже играет!")

            if puid in self.invites:
                return await msg.answer("🤜🏻 Этот человек уже приглашён!")

            if msg.user_id == puid:
                return await msg.answer("🤜🏻 Нельзя вызывать себя!")

            self.invites[puid] = msg.user_id
            self.invites[msg.user_id] = puid

            await self.api.messages.send(peer_id=puid, message=
                f"💭 Вас [id{msg.user_id}|пригласили] для игры в \"{self.game_name}\"!\n"
                f"👉 Напишите {self.prefixes[-1]}{self.c_accept[0]} - чтобы принять вызов.\n"
                f"👉 Напишите {self.prefixes[-1]}{self.c_decline[0]} - чтобы отклонить вызов.\n")

            await self.api.messages.send(peer_id=msg.user_id, message=f"💭 Приглашение отправлено!")

            return

        if command in self.c_decline:
            if msg.user_id in self.invites:
                await self.api.messages.send(peer_id=self.invites[msg.user_id], message=f"💭 Приглашение отклонено!")
                await self.api.messages.send(peer_id=msg.user_id, message=f"💭 Вы отклонили приглашение.")

                del self.invites[self.invites[msg.user_id]]
                del self.invites[msg.user_id]

                return

            return await msg.answer("🤜🏻 У вас нет приглашений!")

        if command in self.c_accept:
            if msg.user_id in self.invites:
                await self.api.messages.send(peer_id=self.invites[msg.user_id], message=f"💭 Игра началась!")
                await self.api.messages.send(peer_id=msg.user_id, message=f"💭 Игра началась!")

                game = {
                    "field": list(["_", "_", "_"] for i in range(3)),
                    "current_turn": int(random.random() * 2),
                    "players": [msg.user_id, self.invites[msg.user_id]],
                    "players_count": 2
                }

                del self.invites[self.invites[msg.user_id]]
                del self.invites[msg.user_id]

                for player in game["players"]:
                    self.games[player] = game

                await self.api.messages.send(
                    peer_id=game["players"][game["current_turn"] % game["players_count"]],
                    message=self.game(game)
                )

                return

        if command in self.c_make_turn:
            game = self.games[msg.user_id]

            if text == "сдаюсь":
                for player in game["players"]:
                    if player == msg.user_id:
                        await self.api.messages.send(peer_id=player, message=f"💭 Вы проиграли!")
                    else:
                        await self.api.messages.send(peer_id=player, message=f"💭 Вы победили!")

                    del self.games[player]

                return

            try:
                x, y = text.split()
            except Exception:
                return await msg.answer("🤜🏻 Введите столб и строку (двумя числами через пробел), куда хотите поставить!")

            if not x.isdigit():
                return await msg.answer("🤜🏻 Столб клетки введён неверно!")

            if not y.isdigit():
                return await msg.answer("🤜🏻 Строка клетки введёна неверно!")

            x = int(x) - 1
            y = int(y) - 1

            if game["field"][y][x] != "_":
                return await msg.answer("🤜🏻 Клетка уже занята!")

            game["field"][y][x] = "X" if game["current_turn"] % 2 else "O"

            won = False

            for i in range(3):
                if i == y:
                    if game["field"][i][0] == game["field"][i][1] == game["field"][i][2]:
                        won = True
                        break

                if i == x:
                    if game["field"][0][i] == game["field"][1][i] == game["field"][2][i]:
                        won = True
                        break

            if not won and x == y:
                if game["field"][0][0] == game["field"][1][1] == game["field"][2][2]:
                    won = True

            if not won and 2 - x == y:
                if game["field"][2][0] == game["field"][1][1] == game["field"][0][2]:
                    won = True

            if won:
                for player in game["players"]:
                    if player == msg.user_id:
                        await self.api.messages.send(peer_id=player, message=self.game(game, controls=False) + "\n💭 Вы победили!")
                    else:
                        await self.api.messages.send(peer_id=player, message=self.game(game, controls=False)  + "\n💭 Вы проиграли!")

                    del self.games[player]

                return

            else:
                over = True

                for i in range(3):
                    for j in range(3):
                        if game["field"][i][j] == "_":
                            over = False
                            break

                if over:
                    for player in game["players"]:
                        if player == msg.user_id:
                            await self.api.messages.send(peer_id=player, message=self.game(game, controls=False) + "\n💭 Ничья!")
                        else:
                            await self.api.messages.send(peer_id=player, message=self.game(game, controls=False) + "\n💭 Ничья!")

                        del self.games[player]

                    return

            game["current_turn"] += 1

            await self.api.messages.send(
                peer_id=game["players"][game["current_turn"] % game["players_count"]],
                message=self.game(game)
            )

            return await msg.answer(self.game(game, controls=False) + "\n💭 Вы сделали свой ход!")
