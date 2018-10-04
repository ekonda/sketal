from plugins import *  # Importing all the plugins from plugins/ folder
from settings_base import BaseSettings  # Importing base settings


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
        StoragePlugin(in_memory=True, save_to_file=True),
        StaffControlPlugin(prefixes=DEFAULT_PREFIXES, admins=DEFAULT_ADMINS, set_admins=True),
        ChatMetaPlugin(),
        UserMetaPlugin(),
        StatisticsPlugin(),

        VoterPlugin(prefixes=DEFAULT_PREFIXES),
        FacePlugin("сделай", prefixes=DEFAULT_PREFIXES),
        SmileWritePlugin(),
        JokePlugin(),
        GraffitiPlugin(),
        QuoteDoerPlugin(),
        WikiPlugin(),
        AnagramsPlugin(),
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
        RandomPostPlugin({"random": -111759315,
            "savehouse": -96322217, "octavia": -36007583}),
        CalculatorPlugin(),
        VideoPlugin(),
        DispatchPlugin(),
        NamerPlugin(),
        help_plugin,

        # Needs tokens (see plugin's codes, some have defaults):
        SayerPlugin(),

        # Plugins for bot's control
        AntifloodPlugin(),
        NoQueuePlugin(),
        CommandAttacherPlugin(),
        ForwardedCheckerPlugin(),
    )

    help_plugin.add_plugins(PLUGINS)
