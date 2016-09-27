import requests


class Plugin:
    vk = None

    plugin_type = 'command'

    def __init__(self, vk):
        self.vk = vk
        print('Курс')

    def getkeys(self):
        keys = ['курс', 'валюта', 'kurs']
        ret = {}
        for key in keys:
            ret[key] = self
        return ret

    def call(self, msg):
        kurs_usd = requests.get("http://api.fixer.io/latest?base=USD")
        kursbid_usd = kurs_usd.json()["rates"]["RUB"]
        kurs_euro = requests.get("http://api.fixer.io/latest?base=EUR")
        kursbid_euro = kurs_euro.json()["rates"]["RUB"]
        kurs_gbp = requests.get("http://api.fixer.io/latest?base=GBP")
        kursbid_gbp = kurs_gbp.json()["rates"]["RUB"]
        vk_message = "1 Доллар = {} руб. \n 1 Евро = {} руб. \n 1 Фунт = {} руб".format(kursbid_usd, kursbid_euro,
                                                                                        kursbid_gbp)

        self.vk.respond(msg, {'message': vk_message})
