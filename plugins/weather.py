import aiohttp
import hues
import time

from plugin_system import Plugin

plugin = Plugin("Погода",
                usage="погода - погода")

# for: https://vk.com/tumkasoff

# сервис для определения погоды: http://openweathermap.org/api
code = "fe198ba65970ed3877578f728f33e0f9"
default_city = "Москва"


text_to_days = {"завтра": 1, "послезавтра": 2, "через день": 2, "через 1 день": 2,
                "через 2 дня": 3, "через 3 дня": 4, "через 4 дня": 5}


@plugin.on_command('погода')
async def weather(msg, args):
    city = default_city
    days = 0

    if args:
        arguments = " ".join(args)

        for k, v in text_to_days.items():
            if k in arguments:
                arguments = arguments.replace(k, "")

                days = v

        possible_city = arguments.replace(" в ", "")

        if possible_city:
            city = possible_city

    if days == 0:
        url = f"http://api.openweathermap.org/data/2.5/weather?APPID={code}&lang=ru&q={city}"
    else:
        url = f"http://api.openweathermap.org/data/2.5/forecast/daily?APPID={code}&lang=ru&q={city}&cnt={days}"

    async with aiohttp.ClientSession() as sess:
        async with sess.get(url) as resp:
            response = await resp.json()

            if days != 0:
                answer = f"{city}. Погода через:\n\n"

                for i in range(len(response["list"])):
                    day = response["list"][i]
                    temperature = day["temp"]["day"] - 273
                    humidity = day["humidity"]
                    description = day["weather"][0]["description"]
                    wind = day["speed"]
                    cloud = day["clouds"]

                    answer += (f'{i + 1} день/я/ей:\n'
                               f'{description[0].upper()}{description[1:]}\n'
                               f'Температура: {round(temperature, 2)} °C\n'
                               f'Влажность: {humidity} %\n'
                               f'Облачность: {cloud} %\n'
                               f'Скорость ветра: {wind} м/с\n\n')

                return await msg.answer(answer)
            else:
                result = response

                description = result["weather"][0]["description"]
                temperature = result["main"]["temp"] - 273
                humidity = result["main"]["humidity"]
                wind = result["wind"]["speed"]
                cloud = result["clouds"]["all"]

                return await msg.answer(f'{city}. Текущая погода.\n'
                                        f'{description[0].upper()}{description[1:]}\n'
                                        f'Температура: {round(temperature, 2)} °C\n'
                                        f'Влажность: {humidity} %\n'
                                        f'Облачность: {cloud} %\n'
                                        f'Скорость ветра: {wind} м/с')
