# Various helpers
import asyncio
import hues


def schedule(seconds):
    def decor(func):
        async def wrapper(*args, **kwargs):
            while True:
                await asyncio.sleep(seconds)
                await func(*args, **kwargs)

        return wrapper

    return decor


# http://stackoverflow.com/questions/312443/how-do-you-split-a-list-into-evenly-sized-chunks
def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]


class Attachment(object):
    __slots__ = ('type', 'owner_id', 'id')

    def __init__(self, type: str, owner_id: int, aid: int):
        self.type = type
        self.owner_id = owner_id
        self.id = aid

    def __repr__(self):
        return "<Attachment with type '{}', owner '{}', id '{}'>".format(
            self.type, self.owner_id, self.id
        )


class MessageEventData(object):
    # __slots__ используется для оптимизации объектов этого класса
    __slots__ = ('conf', 'peer_id', 'user_id', 'body', 'time', 'attaches')

    def __init__(self, conf: bool, pid: int, uid: int, body: str, attaches: dict, time: int):
        self.conf = conf
        self.peer_id = pid
        self.user_id = uid
        self.body = body
        self.time = time
        self.attaches = []
        if 'attach1' not in attaches:
            # Нет ни одного приложения
            return
        for k, v in attaches.items():
            if '_type' not in k:
                try:
                    type = attaches[k + '_type']
                except KeyError:
                    # Могут быть такие ключи, как 'from', т.е. не только приложения
                    continue
                owner_id, id = v.split('_')
                self.attaches.append(Attachment(type, owner_id, id))

    def __repr__(self):
        return self.body


def fatal(*args):
    """Отправляет args в hues.error() и выходит"""
    hues.error(*args)
    exit()


# Characters are taken from http://gsgen.ru/tools/perevod-raskladki-online/
english = "Q-W-E-R-T-Y-U-I-O-P-A-S-D-F-G-H-J-K-L-Z-X-C-V-B-N-M"
eng_expr = english + english.lower() + "-" + ":-^-~-`-{-[-}-]-\"-'-<-,->-.-;-?-/-&-@-#-$"
russian = "Й-Ц-У-К-Е-Н-Г-Ш-Щ-З-Ф-Ы-В-А-П-Р-О-Л-Д-Я-Ч-С-М-И-Т-Ь"
rus_expr = russian + russian.lower() + "-" + "Ж-:-Ё-ё-X-x-Ъ-ъ-Э-э-Б-б-Ю-ю-ж-,-.-?-\"-№-;"

translate_table = str.maketrans(eng_expr, rus_expr)
en_trans = str.maketrans(rus_expr, eng_expr)


def convert_to_rus(text: str) -> str:
    """Конвертировать текст, написанный на русском с английской раскладкой в русский"""
    return text.translate(translate_table)


def convert_to_en(text: str) -> str:
    """Конвертировать текст, написанный на русском с русской раскладкой в английскую раскладку"""
    return text.translate(en_trans)


keys = [
    'unread',
    'outbox',
    'replied',
    'important',
    'chat',
    'friends',
    'spam',
    'deleted',
    'fixed',
    'media'
]


def parse_msg_flags(bitmask: int) -> dict:
    """Функция для чтения битовой маски и возврата словаря значений"""
    start = 1
    values = []
    for x in range(1, 11):
        result = bitmask & start
        start *= 2
        values.append(bool(result))
    return dict(zip(keys, values))
