from plugins import *  # Importing all the plugins from plugins/ folder

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
    DEFAULTS["PREFIXES_STRICT"] = False
    DEFAULTS["ADMINS"] = DEFAULT_ADMINS = ()  # (admin_id_1,) !Comma is required even if only element

    # Plugins
    PLUGINS = ()
