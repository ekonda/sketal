import sys, bot


if __name__ == "__main__":
    try:
        if "-d" in sys.argv:
            raise ModuleNotFoundError

        from settings_prod import BotSettings

    except ModuleNotFoundError:
        from settings import BotSettings

    bot = bot.Bot(BotSettings)
    bot.longpoll_run()

    # Or choose a better way for you:
    # bot.longpoll_run()
    # bot.bots_longpoll_run()
    # bot.callback_run()
