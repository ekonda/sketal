import sys, os


class BasePlugin:
    __slots__ = ("bot", "handler", "api", "name", "description")

    def __init__(self):
        self.bot = None
        self.api = None
        self.handler = None

        if not hasattr(self, "name"):
            self.name = self.__class__.__name__

        if not hasattr(self, "description"):
            self.description = ""

    def get_path(self, path):
        """You can use this method to load files from your plugin's folder"""

        if path.startswith("/"):
            path = path[1:]

        return os.path.join(os.path.dirname(sys.modules[self.__module__].__file__), path)

    def set_up(self, bot, api, handler):
        """Here plugin gets his bot and vk instances to work with"""

        self.bot = bot
        self.api = api
        self.handler = handler

    def preload(self):
        """ Very first thing any plugin executes
        """
        pass

    def initiate(self):
        """ Initiation of plugin.
        (see `bot.do()` for async methods here)
        """
        pass

    # # # # # # # # # # # # # # # # # # # # # # # # #
    async def check_message(self, msg):
        """ Returns `True` if message `msg` should be processed by this plugin
        """

        return False

    async def global_before_message_checks(self, msg):
        """ Takes Message `msg` as argument and returns `True` if message should be processed or
        `False` if nothing should be processed

        Executed before message was checked
        """

        return True

    async def global_before_message(self, msg, plugin):
        """ Takes Message `msg`, plugin currently working with message `plugin` and returns
        `True` if message should be processed

        Executed before any message was processed
        """

        return True

    async def global_after_message(self, msg, plugin, result):
        """Executed after message `msg` was processed by plugin `plugin`"""

        pass

    async def process_message(self, msg):
        """Processes message `msg` and returns `False` if message should be passed to other plugins"""

        pass

    # # # # # # # # # # # # # # # # # # # # # # # # #
    async def check_event(self, evnt):
        """Returns `True` if event `evnt` should be processed by this plugin"""

        return False

    async def global_before_event_checks(self, evnt):
        """ Takes event `evnt` and returns `True` if event should be processed or
        `False` if nothing should be processed

        Executed before message was checked
        """

        return True

    async def global_before_event(self, evnt, plugin):
        """ Takes event `evnt`, plugin currently working with message `plugin` and returns `True` if this event
        should be processed

        Executed before any event was processed
        """

        return True

    async def global_after_event(self, evnt, plugin, result):
        """Executed after event `evnt` was processed by plugin `plugin` with result `result`"""

        pass

    async def process_event(self, evnt):
        """Processes event `evnt` and returns `False` if event should be passed to other plugins"""

        pass

    def stop(self):
        pass
