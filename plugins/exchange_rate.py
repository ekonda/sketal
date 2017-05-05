import aiohttp

from plugin_system import Plugin

plugin = Plugin('Курсы валют',
                usage=['курс - узнать курс доллара, евро, и фунта к рублю'])


async def get_rate(first: str, to: str = "RUB"):
    async with aiohttp.ClientSession() as sess:
        async with sess.get(f"http://api.fixer.io/latest?base={first}") as resp:
            try:
                data = await resp.json()
                return data['rates'][to]
            except (KeyError, IndexError):
                raise ValueError('Курса данной валюты не найдено')


@plugin.on_command('курс', 'валюта')
async def get_rates(msg, args):
    data = []
    for cur in ('USD', 'EUR', 'GBP'):
        data.append(await get_rate(cur))
    usd, eur, gbp = data
    vk_message = (f"1 Доллар = {usd} руб.\n"
                  f"1 Евро = {eur} руб.\n"
                  f"1 Фунт = {gbp} руб\n")
    await msg.answer(vk_message)
