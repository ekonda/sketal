class BaseSettings:
    USERS = ()
    PROXIES = ()
    CONF_CODE = ""
    SCOPE = 140489887
    APP_ID = 5982451
    CAPTCHA_KEY = ""
    CAPTCHA_SERVER = "rucaptcha"
    READ_OUT = False
    PLUGINS = ()

    DEBUG = False

    # Заполнять ниже `BotSettings`


class BotSettings(BaseSettings):
    USERS = (
        ("group", "API КЛЮЧ СООБЩЕСТВА",),
    )

    PROXIES = (
        # ("ADDRESS", "LOGIN", "PASSWORD", "ENCODING),
    )

    # Code for Callback Api

    CONF_CODE = ""

    # VK information

    SCOPE = 140489887
    APP_ID = 5982451

    # Captcha solver's data

    CAPTCHA_KEY = ""
    CAPTCHA_SERVER = "rucaptcha"

    # Database

    DATABASE_NAME = ""
    DATABASE_HOST = ""
    DATABASE_USER = ""
    DATABASE_PASSWORD = ""
    DATABASE_PORT = 0

    DATABASE_TABLES_PREFIX = ""

    # Other

    READ_OUT = False

    # Plugins

    # Plugin's main class names must by unique!

    # You can import needed plugins in any way possible by Python
    # Exmaple: `from plugins.about import AboutPlugin`
    #
    # You can import any plugins inside `plugins` using special bot-specific package:
    # from plugin import AboutPlugin
    #
    # You can import all plugins as once using `from plugins import *` at module-level.

    from plugins import AboutPlugin, BirthdayPlugin, MembersPlugin, PairPlugin, WhoIsPlugin, YandexNewsPlugin, \
                            HelpPlugin, TimePlugin, DispatchPlugin, ResendCommanderPlugin, QRCodePlugin, \
                            RandomPostPlugin, ChatKickerPlugin, CalculatorPlugin, ResendCheckerPlugin, ChatterPlugin

    from plugins import HangmanPlugin
    from plugins import ToptextbottomtextPlugin

    prefixes = ("!", "бот ", "бот, ", "бот,")
    admins = (87641997, )

    hp = HelpPlugin("помощь", "команды", "?", prefixes=prefixes)

    PLUGINS = (
        HangmanPlugin("виселица", prefixes=prefixes),
        MembersPlugin("кто тут", prefixes=prefixes),
        PairPlugin("кто кого", prefixes=prefixes),
        WhoIsPlugin("кто", prefixes=prefixes),
        YandexNewsPlugin(["новости"], ["помощь", "категории", "?"], prefixes=prefixes),
        AboutPlugin("о боте", "инфа", prefixes=prefixes),
        BirthdayPlugin("дни рождения", "др", prefixes=prefixes),
        DispatchPlugin("рассылка", prefixes=prefixes, admins=admins),
        TimePlugin("время", prefixes=prefixes),
        ToptextbottomtextPlugin("мем", "свой текст", prefixes=prefixes),
        QRCodePlugin("qr", "кр", prefixes=prefixes),
        ChatKickerPlugin(["кик"], ["фри", "анкик"], prefixes=prefixes, admins=admins, admins_only=True),
        RandomPostPlugin({"random": "-111759315", "memes": "-77127883", "мемы": "-77127883"}, prefixes=prefixes),
        CalculatorPlugin("посчитай", "посч", prefixes=prefixes),
        hp,

        ResendCommanderPlugin(), ChatterPlugin(prefixes=prefixes),

        ResendCheckerPlugin(),
    )

    hp.add_plugins(PLUGINS)
