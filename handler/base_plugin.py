import sys, os, re

DEFAULTS = {}

class BasePlugin:
    __slots__ = ("bot", "handler", "api", "name", "description", "order")

    def __init__(self):
        self.bot = None
        self.api = None
        self.handler = None

        # order for (global_before_*_checks, global_after_*_process)
        # -100 -> absolutly first
        # 100 -> absolutly last
        self.order = (0, 0)

        if not hasattr(self, "name"):
            self.name = self.__class__.__name__

        if not hasattr(self, "description"):
            self.description = ""

    def get_path(self, path):
        """You can use this method to load files from your plugin's folder."""

        if path.startswith("/"):
            path = path[1:]

        return os.path.join(os.path.dirname(sys.modules[self.__module__].__file__), path)

    def set_up(self, bot, api, handler):
        """Here plugin gets his bot and vk instances to work with."""

        self.bot = bot
        self.api = api
        self.handler = handler

    def preload(self):
        """Very first thing any plugin executes."""
        pass

    def initiate(self):
        """Initiation of plugin (see `bot.do()` for async methods here)."""
        pass

    # # # # # # # # # # # # # # # # # # # # # # # # #
    async def check_message(self, msg):
        """Returns `True` if message `msg` should be processed by this plugin."""
        return False

    async def global_before_message_checks(self, msg):
        """Takes Message `msg` as argument and returns `True` if message should
        be processed or `False` if nothing should be processed.
        Executedbefore message was checked."""
        return True

    async def global_after_message_process(self, msg, result):
        """Takes Message `msg` and message process result `result` as arguments.
        Executed after message was checked and processed.
        If `False` is returned processes will stop."""
        return True

    async def global_before_message(self, msg, plugin):
        """Takes Message `msg`, plugin currently working with message `plugin`
        and returns `True` if message should be processed. Executed before
        any message was processed."""
        return True

    async def global_after_message(self, msg, plugin, result):
        """Executed after message `msg` was processed by plugin `plugin`."""
        pass

    async def process_message(self, msg):
        """Processes message `msg` and returns `False` if message should be
        passed to other plugins."""
        pass

    # # # # # # # # # # # # # # # # # # # # # # # # #
    async def check_event(self, evnt):
        """Returns `True` if event `evnt` should be processed by this plugin."""
        return False

    async def global_before_event_checks(self, evnt):
        """Takes Event `evnt` and returns `True` if event should be processed
        or `False` if nothing should be processed.
        Executed before event was checked."""
        return True

    async def global_after_event_process(self, evnt, result):
        """Takes Event `evnt` and event process result `result` as arguments.
        Executed after event was checked and processed.
        If `False` is returned processes will stop."""
        return True

    async def global_before_event(self, evnt, plugin):
        """Takes event `evnt`, plugin currently working with message `plugin`
        and returns `True` if this event should be processed. Executed before
        any event was processed."""
        return True

    async def global_after_event(self, evnt, plugin, result):
        """Executed after event `evnt` was processed by plugin `plugin` with
        result `result`."""
        pass

    async def process_event(self, evnt):
        """Processes event `evnt` and returns `False` if event should be passed
        to other plugins."""
        pass

    def stop(self):
        pass


class CommandPlugin(BasePlugin):
    __slots__ = ("commands",  "compiled_commands", "prefixes",
        "compiled_prefixes", "strict")

    def __init__(self, *commands, prefixes=None, strict=False):
        super().__init__()

        self.strict = strict

        self.commands = commands if strict else [command.strip().lower() for command in commands]
        self.commands = sorted(self.commands, key=len, reverse=True)  # или x.count(" ")?

        self.compiled_commands = []
        for command in self.commands:
            if self.strict:
                pattern = re.compile(rf"^{re.escape(command)}( +|\n+|$)")
            else:
                pattern = re.compile(rf"^{re.escape(command)}( +|\n+|$)", re.I)

            self.compiled_commands.append(pattern)

        self.prefixes = prefixes if prefixes else DEFAULTS["PREFIXES"]
        self.prefixes = sorted(self.prefixes, reverse=True)

        self.compiled_prefixes = []
        for prefix in self.prefixes:
            self.compiled_prefixes.append(
                re.compile(rf"^{re.escape(prefix)}", re.I))

    def command_example(self, command_index=0):
        return f"{self.prefixes[-1] if self.prefixes else ''}{self.commands[command_index]}"

    @staticmethod
    def parse_message(msg, full_text=None):
        """Returns message without command from Message object"""

        return msg.meta["__command"], (msg.meta["__arguments_full"]
            if full_text else msg.meta["__arguments"])

    async def check_message(self, msg):
        if msg.meta.get("__no_prefix"):
            return False

        if any(e not in msg.meta for e in ("__prefix", "__raw_text", "__raw_full_text")):
            for prefix, pattern in zip(self.prefixes, self.compiled_prefixes):
                match = pattern.match(msg.text)

                if match:
                    msg.meta["__prefix"] = prefix
                    msg.meta["__raw_text"] = msg.text[match.end():].strip()
                    msg.meta["__raw_full_text"] = msg.full_text[match.end():].strip()

                    msg.meta["__no_prefix"] = False

                    break

            else:
                msg.meta["__no_prefix"] = True
                return False

        for command, pattern in zip(self.commands, self.compiled_commands):
            match = pattern.match(msg.meta["__raw_full_text"])

            if match:
                msg.meta["__command"] = command
                msg.meta["__arguments"] = msg.meta["__raw_text"] \
                    [match.end():].strip()
                msg.meta["__arguments_full"] = msg.meta["__raw_full_text"] \
                    [match.end():].strip()

                return True

        return False

    async def process_message(self, msg):
        await msg.answer("Команда: (" + ", ".join(self.commands) + ")")
