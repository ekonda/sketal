# Various helpers
import hues


def fatal(*args):
    '''Passes args to hues.error and then exits'''
    hues.error(*args)
    exit()


# Strings are taken from http://tinklai.dkd.lt/papildomai/belib-rus
english = "Q-W-E-R-T-Y-U-I-O-P-A-S-D-F-G-H-J-K-L-Z-X-C-V-B-N-M"
russian = "Й-Ц-У-К-Е-Н-Г-Ш-Щ-З-Ф-Ы-В-А-П-Р-О-Л-Д-Я-Ч-С-М-И-Т-Ь"
english = ''.join(english + english.lower())
russian = ''.join(russian + russian.lower())
# russian = r'''йцукенгшщзхъ\фывапролджэячсмитьбю.ёЙЦУКЕНГШЩЗХЪ/ФЫВАПРОЛДЖЭЯЧСМИТЬБЮ?Ё!"№;%:?*()_+'''
# english = r'''qwertyuiop[]\asdfghjkl;'zxcvbnm,./`QWERTYUIOP{}|ASDFGHJKL:"ZXCVBNM<>?~!@#$%^&*()_+'''

translate_table = str.maketrans(english, russian)
en_trans = str.maketrans(russian, english)


def convert_to_rus(text: str) -> str:
    '''Конвертировать текст, написанный на русском с английской раскладкой в русский'''
    return text.translate(translate_table)


def convert_to_en(text: str) -> str:
    '''Конвертировать текст, написанный на русском с русской раскладкой в английскую раскладку'''
    return text.translate(en_trans)
