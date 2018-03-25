from handler.base_plugin_command import CommandPlugin

from geopy.geocoders import Photon, Yandex, Nominatim
import aiohttp

import json, time

# Powered by Dark Sky, https://darksky.net


class WeatherPlugin(CommandPlugin):
    __slots__ = ("geocoders", "icons", "token", "coords_cache", "weather_cache",
                 "weather_clear", "api_lim", "api_lim_clear", "api_lim_count")

    def __init__(self, *commands, token=None, prefixes=None, strict=False):
        """Answers with a weather in user's city or on specified addres."""

        if not token:
            raise ValueError("Token is not specified! Get it from: https://darksky.net")

        super().__init__(*commands, prefixes=prefixes, strict=strict)

        self.token = token

        self.icons = {
        	"clear-day": "☀️",
        	"clear-night": "🌙",
        	"cloudy": "☁️",
        	"fog": "🌁",
        	"partly-cloudy-day":   "⛅️",
        	"partly-cloudy-night": "🌙",
        	"rain": "☔️",
        	"sleet": "❄️ ☔️",
        	"snow": "❄️",
        	"wind": "🍃",
        	"error": "🤔",
        }

        self.geocoders = []
        for coder in [Photon, Yandex, Nominatim]:
            self.geocoders.append(coder())

        self.coords_cache = {}
        self.weather_cache = {}
        self.weather_clear = time.time() + 12 * 60 * 60

        self.api_lim = 95
        self.api_lim_clear = time.time() + 24 * 60 * 60
        self.api_lim_count = 0

    async def get_weather(self, result):
        if self.weather_clear - time.time() <= 0:
            self.weather_clear = time.time() + 12 * 60 * 60
            self.weather_cache.clear()

        if f"{result.latitude}_{result.longitude}" in self.weather_cache:
            return self.weather_cache[f"{result.latitude}_{result.longitude}"]

        url = "https://api.darksky.net/forecast/{token}/{latitude},{longitude}?lang=ru&units=si&exclude=minutely,currently,alerts,flags"

        if self.api_lim_clear - time.time() <= 0:
            self.api_lim_clear = time.time() + 24 * 60 * 60
            self.api_lim_count = 0

        if self.api_lim_count >= self.api_lim:
            return "LIMIT EX"

        self.api_lim_count += 1

        async with aiohttp.ClientSession() as sess:
            async with sess.get(url.format(token=self.token,
                                           latitude=result.latitude,
                                           longitude=result.longitude)) as resp:
                try:
                    w = json.loads(await resp.text())
                except json.decoder.JSONDecodeError:
                    return None

        if len(self.weather_cache) > 400 and self.api_lim_count < self.api_lim:
            self.weather_cache.clear()

        self.weather_cache[f"{result.latitude}_{result.longitude}"] = w

        return w

    async def get_coords(self, text):
        if text in self.coords_cache:
            return self.coords_cache[text]

        for i in range(len(list(self.geocoders))):
            result = self.geocoders[-1].geocode(text)

            if not result: continue

            if i != 0:
                self.geocoders[0], self.geocoders[i] = self.geocoders[i], self.geocoders[0]

            if len(self.coords_cache) > 400:
                self.coords_cache.clear()

            self.coords_cache[text] = result

            return result

        return None

    async def process_message(self, msg):
        command, text = self.parse_message(msg)

        if not text:
            user = await self.api.users.get(user_ids=msg.user_id, fields="city,country")

            if len(user) > 0:
                user = user[0]

            try:
                city = user["city"]["title"]
            except KeyError:
                city = ""

            try:
                country = user["country"]["title"]
            except KeyError:
                country = ""

            text = (country + " " + city).strip()

        if not text:
            return await msg.answer("У вас не найден город! Простите :(")

        result = await self.get_coords(text)
        if not result: return await msg.answer("Ваши координаты не найдёны!")

        w = await self.get_weather(result)
        if w == "LIMIT EX": return await msg.answer("Больше новых прогнозов сегодня не будет! Приходите завтра.")
        if not w: return await msg.answer("Ошибка! Погода не найдена!")

        h = w['hourly']
        hd = h["data"][len(h["data"]) // 2]

        text = self.icons[h["icon"]] * 5 + "\n"
        text += f"🌍 Долгота / широта: {result.longitude} / {result.latitude}\n"
        text += f"💬 {h['summary']} {w['daily']['summary']}\n"

        if "humidity" in hd:
            text += f"💧 Влажность: {round(hd['humidity'] * 100, 2)} %\n"

        if "pressure" in hd:
            text += f"📐 Давление: {hd['pressure'] / 1000.0} бар\n"

        if "windSpeed" in hd:
            text += f"💨 Скорость ветра: {hd['windSpeed']} м/с\n"

        if "visibility" in hd:
            text += f"👀 Видимость: {hd['visibility']} км\n"

        text += self.icons[h["icon"]] * 5 + "\n"

        return await msg.answer(text)
