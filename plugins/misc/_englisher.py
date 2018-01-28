# Remove _ before this module's name to activate it
# It will turn all answers except commands (can be turned off) to english translit

from transliterate import translit


def main(save_commands):
    import vk.data, re
    original_answer = vk.data.Message.answer

    async def repl(self, message="", wait=None, **additional_values):
        newmessage = ""

        if save_commands and message:
            try:
                ps = self.api.settings.prefixes
                pa = "((" + "|".join("(" + re.escape(p) + ")" for p in ps) + ").*?(\n|-|\"|'))"
                lp = 0

                for m in re.finditer(pa, message):
                    newmessage += translit(message[lp:m.start()], 'ru', reversed=True)
                    newmessage += message[m.start():m.end()]
                    lp = m.end()

                if lp < len(message):
                    newmessage += translit(message[lp:], 'ru', reversed=True)

            except AttributeError:
                pass

        if not newmessage and message:
            newmessage = translit(message, 'ru', reversed=True)

        return await original_answer(self, newmessage, wait, **additional_values)

    vk.data.Message.answer = repl

if (__name__.split(".")[-1][0]) != "_":
    main(save_commands=True)
