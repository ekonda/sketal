import requests
from plugin_system import Plugin

plugin = Plugin('Курсы валют')


@plugin.on_command('курс', 'валюта', 'какой курс?')
async def kurs_get(vk, msg, args):
    kurs_usd = requests.get("http://api.fixer.io/latest?base=USD")
    kursbid_usd = kurs_usd.json()["rates"]["RUB"]
    kurs_euro = requests.get("http://api.fixer.io/latest?base=EUR")
    kursbid_euro = kurs_euro.json()["rates"]["RUB"]
    kurs_gbp = requests.get("http://api.fixer.io/latest?base=GBP")
    kursbid_gbp = kurs_gbp.json()["rates"]["RUB"]
    vk_message = "1 Доллар = {} руб. \n 1 Евро = {} руб. \n 1 Фунт = {} руб".format(kursbid_usd, kursbid_euro,
                                                                                    kursbid_gbp)
    await vk.respond(msg, {'message': vk_message})
