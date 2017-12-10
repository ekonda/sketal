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


from plugins import *


class BotSettings(BaseSettings):
    USERS = (
        ("group", "ТУТ ТОКЕН ГРУППЫ",),
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
    # You can import all plugins at once using `from plugins import *` at module-level.

    prefixes = ("!", "бот ", "бот, ", "бот,")
    admins = (87641997, )

    hp = HelpPlugin("помощь", "команды", "?", prefixes=prefixes)

    PLUGINS = (
        AdminPlugin(prefixes=prefixes, admins=admins, setadmins=True),

        RememberPlugin("напомни",prefixes=prefixes),
        # WeatherPlugin("погода", token="token for api", prefixes=prefixes),
        QuotePlugin("цитатка"),
        WikiPlugin("что такое", prefixes=prefixes),
        AnagramsPlugin(["анаграмма", "анаграммы"], prefixes=prefixes),
        HangmanPlugin(["виселица"], prefixes=prefixes),
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
        SayerPlugin("скажи", prefixes=prefixes),
        hp,

        ChatterPlugin(prefixes=prefixes),

        ResendCommanderPlugin(), ResendCheckerPlugin(),
    )

    hp.add_plugins(PLUGINS)
