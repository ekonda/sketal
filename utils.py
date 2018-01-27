import datetime
import html

import json
from dateutil.relativedelta import relativedelta


def traverse(o, tree_types=(list, tuple)):
    if isinstance(o, tree_types):
        for value in o:
            for subvalue in traverse(value, tree_types):
                yield subvalue
    else:
        yield o


cases = (2, 0, 1, 1, 1, 2)


def plural_form(n: int, v: (list, tuple)):
    """Функция возвращает число и просклонённое слово после него

    Аргументы:
    :param n: число
    :param v: варианты слова в формате (для 1, для 2, для 5)

    Пример:
    plural_form(difference.days, ("день", "дня", "дней"))

    :return: Число и просклонённое слово после него
    """

    return f"{n}  {v[2 if (4 < n % 100 < 20) else cases[min(n % 10, 5)]]}"


def age(date):
    """Возвращает возраст в годах по дате рождения

    Функция
    :param date: дата рождения
    :return: возраст
    """

    # Get the current date
    now = datetime.datetime.utcnow()
    now = now.date()

    # Get the difference between the current date and the birthday
    res = relativedelta(now, date)
    return res.years


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
    'media',
    'hidden'
]


def parse_msg_flags(bitmask, keys=('unread', 'outbox', 'replied', 'important', 'chat',
                                   'friends', 'spam', 'deleted', 'fixed', 'media', 'hidden')):
    """Функция для чтения битовой маски и возврата словаря значений"""

    start = 1
    values = []
    for _ in range(1, 12):
        result = bitmask & start
        start *= 2
        values.append(bool(result))
    return dict(zip(keys, values))


def unquote(data: (str, dict, list)):
    """Функция, раскодирующая ответ от ВК

    :param data: строка для раскодировки
    :return: раскодированный ответ
    """

    temp = data

    if issubclass(temp.__class__, str):
        return html.unescape(html.unescape(temp))

    if issubclass(temp.__class__, dict):
        for k, v in temp.items():
            temp[k] = unquote(v)

    if issubclass(temp.__class__, list):
        for i, e in enumerate(len(temp)):
            temp[i] = unquote(e)

    return temp


def json_iter_parse(response_text):
    decoder = json.JSONDecoder(strict=False)
    idx = 0
    while idx < len(response_text):
        obj, idx = decoder.raw_decode(response_text, idx)
        yield obj
