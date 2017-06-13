import difflib
from random import choice

from chatterbot import ChatBot


class ConditionModel:
    def check(self, chat_data):
        pass


class Searcher(ConditionModel):
    __slots__ = ("conditions",)
    all = True

    def __init__(self, texts: (str, list), compare, i: int):
        if isinstance(texts, str):
            texts = [texts]

        self.conditions = []

        for text in texts:
            self.conditions.append(One(text, compare, i))

    def check(self, chat_data):
        for condition in self.conditions:
            if condition.check(chat_data):
                if not self.all:
                    return True
            else:
                if self.all:
                    return False

        return self.all


class All(Searcher):
    all = True


class Any(Searcher):
    all = False


class One(ConditionModel):
    __slots__ = ("x", )

    def __init__(self, text: str, compare, i: int):
        self.x = i, text, compare

    def check(self, chat_data):
        i, text, compare = self.x

        if len(chat_data) <= i:
            return compare("", text)

        return compare(chat_data[i], text)


class Two(ConditionModel):
    __slots__ = ("x", "y", "compare")

    def __init__(self, x: ConditionModel, y: ConditionModel, compare):
        self.x = x
        self.y = y
        self.compare = compare

    def check(self, chat_data):
        x = self.x.check(chat_data)
        y = self.y.check(chat_data)

        return self.compare(x, y)


#####################################################################################
def normalize(string):
    return string.strip().lower()


class Compare:
    @staticmethod
    def equals(x: str, y: str):
        return x == y

    @staticmethod
    def inside(x: str, y: str):
        return y in x

    @staticmethod
    def close(x: str, y: str):
        return difflib.SequenceMatcher(None, x, y).ratio() > 0.8

    @staticmethod
    def not_equals(x: str, y: str):
        return x != y

    @staticmethod
    def not_inside(x: str, y: str):
        return y not in x

    @staticmethod
    def not_close(x: str, y: str):
        return difflib.SequenceMatcher(None, x, y).ratio() <= 0.8


class Join:
    @staticmethod
    def anything(x: bool, y: bool):
        return x or y

    @staticmethod
    def everything(x: bool, y: bool):
        return x and y

    @staticmethod
    def nothing(x: bool, y: bool):
        return not x and not y


#####################################################################################
class Dialog:
    __slots__ = ("condition", "answer")

    def __init__(self, condition, *answer):
        self.condition = condition
        self.answer = answer

    def set(self, condition):
        self.condition = condition

    def check(self, chat_data):
        return self.condition.check(chat_data)


class Chatter:
    __slots__ = ("dialogs", )

    def __init__(self):
        self.dialogs = []

    def add(self, *dialog):
        if isinstance(dialog[0], Dialog):
            return self.dialogs.append(dialog)

        return self.dialogs.append(Dialog(*dialog))

    def parse_message(self, chat_data):
        for dialog in self.dialogs:
            if dialog.check(chat_data):
                return choice(dialog.answer)

        return None


class ChatterBot:
    __slots__ = ("chatbot", )

    def __init__(self):
        self.chatbot = ChatBot(
            'Валера',
            trainer='chatterbot.trainers.ChatterBotCorpusTrainer'
        )

        self.chatbot.train("chatterbot.corpus.russian")

    def parse_message(self, chat_data):
        return str(self.chatbot.get_response(chat_data[0]))
