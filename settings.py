from plugins import *  # Importing all the plugins from plugins/ folder

# ------------------------------------------------------------------------------
# Base settings. Your settings should be written at least in BotSettings (lower)
# ------------------------------------------------------------------------------
class BaseSettings:
    USERS = ()  # Private VK info
    PROXIES = ()  # Private proxies info

    CONF_CODE = ""  # Code for Callback Api (if you use it)

    SCOPE = 140489887  # Not private VK info
    APP_ID = 5982451  # Not private VK info

    CAPTCHA_KEY = ""  # Captcha solver's data
    CAPTCHA_SERVER = "rucaptcha"  # Captcha solver's data

    # Some settings
    READ_OUT = False
    DEBUG = False
    DEFAULTS["PREFIXES"] = DEFAULT_PREFIXES = ("/",)
    DEFAULTS["ADMINS"] = DEFAULT_ADMINS = ()  # (admin_id_1,) !Comma is required even if only element

    # Plugins
    PLUGINS = ()


# ------------------------------------------------------------------------------
# Settings that bot will use!
# ------------------------------------------------------------------------------
class BotSettings(BaseSettings):
    # See README.md for details!
    USERS = (
        ("user", "ТУТ ТОКЕН ПОЛЬЗОВАТЕЛЯ",),
    )

    # Default settings for plugins
    DEFAULTS["PREFIXES"] = DEFAULT_PREFIXES = ("/",)
    DEFAULTS["ADMINS"] = DEFAULT_ADMINS = (87641997, )

    # You can setup plugins any way you like. See plugins's classes and README.md.
    # All available plugins can be found in folder `plugins` or in file `PLUGINS.md`.
    # Bot will use all plugins inside PLUGINS variable.
    help_plugin = HelpPlugin("помощь", "команды", "?", prefixes=DEFAULT_PREFIXES)

    # List of active plugins
    PLUGINS = (
        AdminPlugin(prefixes=DEFAULT_PREFIXES, admins=DEFAULT_ADMINS, setadmins=True),
        ChatMetaPlugin(),

        VoterPlugin(prefixes=DEFAULT_PREFIXES),
        FacePlugin("сделай", prefixes=DEFAULT_PREFIXES),
        SmileWritePlugin(),
        JokePlugin(),
        GraffitiPlugin(),
        QuoteDoerPlugin(),
        WikiPlugin(),
        MembersPlugin(),
        PairPlugin(),
        WhoIsPlugin(),
        YandexNewsPlugin(),
        AboutPlugin(),
        BirthdayPlugin(),
        TimePlugin(),
        MemeDoerPlugin(),
        QRCodePlugin(),
        ChatKickerPlugin(admins_only=True),
        RandomPostPlugin({"kitties": -145935681, "random": -111759315,
            "savehouse": -96322217, "octavia": -36007583}),
        CalculatorPlugin(),
        VideoPlugin(),
        DispatchPlugin(),
        help_plugin,

        # Needs tokens (see plugin's codes, some have defaults):
        SayerPlugin(),

        # Plugins for bot's control
        AntifloodPlugin(),
        CommandAttacherPlugin(),
    )

    help_plugin.add_plugins(PLUGINS)
