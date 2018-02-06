<p align="center">
    <img src="https://github.com/vk-brain/sketal/blob/master/docs/title.png?raw=true" alt="vk-sketal logo"/>
</p>

## sketal

[![Codacy Badge](https://api.codacy.com/project/badge/Grade/1a5af7a2447a4f83838cb4ea9da0bb43)](https://www.codacy.com/app/m-krjukov/Sketal?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=vk-brain/sketal&amp;utm_campaign=Badge_Grade) [![Build Status](https://travis-ci.org/vk-brain/sketal.svg?branch=master)](https://travis-ci.org/vk-brain/sketal)

#### Немного о боте
- Бот работает на python3.6 и выше. Ниже не работает. **Совсем**. Это важно.
- Бот использует asyncio, aiohttp и т.д.

#### Инструкция
1. Скачать бота.

2. Скачать Python версии 3.6 или выше.

3. Установить модули для python. Список модулей находится в `requirements.txt`.
   ```
   python -m pip install -r requirements.txt
   ```

4. Настроить бота в `settings.py`. Обязательно для заполнения только поле USERS.

   **Обращайте внимание на запятые и кавычки! Это важно.**

5. Запустить бота **из командной строки** **из папки с ботом**.
   ```
   python bot.py
   ```

[Более подробная инструкция.](docs/start.md)

#### Документация
Как таковой документации проект сейчас не имеет. Многие функции, примеры, возможности бота можно найти, изучая исходный код плагинов и файлы бота. Например: `tests.py`, `vk/helpers.py`, `handler/base_plugin.py` и т.д.

#### Материалы:
- [Sketal. Быстрый ввод в разработку плагинов.](https://vk.com/@vkbraindev-quick-dev-start)
- [Как бесплатно захостить Sketal (деплой на Heroku).](http://disonds.com/2018/01/31/razviertyvaniie-python-bota-sketal-dlia-vkontaktie-na-heroku/)

#### Замечания
-  Никакие плагины не должны менять код основных частей бота, чтобы было легко обновляться и менять какие-то базовые вещи (переписывать плагины легче, чем восстанавливать функционал после обновлений).
- При использовании CommandPlugin помните, что команды сортируются в соответствии с количесвом пробелов в команде (от большего к меньшему)
- Многие плагины требуют `PeeweePlugin` (база данных).
- Крайне рекомендуется использовать `AdminPlugin` (контроль привилегий).

#### Участники проекта:
- [Список участников (все молодцы! большие!)](https://github.com/vk-brain/sketal/graphs/contributors)
- [Плагинчик сделал](https://github.com/TumkasCor)
- [Плагинчик сделал](https://github.com/Lis1us)

@michaelkrukov http://michaelkrukov.ru/
