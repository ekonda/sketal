import requests
from plugin_system import Plugin

plugin = Plugin('Курсы валют',
                usage='курс - узнать курс доллара, евро, и фунта к рублю\n'
                      'сколько {валюты} в {кол-во} {валюте} - узнать курс между 2 валютами')


def get_rate(first: str, to: str = "RUB"):
    rate = requests.get(f"http://api.fixer.io/latest?base={first}")
    try:
        return rate.json()["rates"][to]
    except (KeyError, IndexError):
        raise ValueError('Курса данной валюты не найдено')


@plugin.on_command('курс', 'валюта')
async def get_rates(msg, args):
    usd, eur, gbp = (get_rate(cur) for cur in ('USD', 'EUR', 'GBP'))
    vk_message = (f"1 Доллар = {usd} руб.\n"
                  f"1 Евро = {eur} руб.\n"
                  f"1 Фунт = {gbp} руб\n")
    await msg.answer(vk_message)
