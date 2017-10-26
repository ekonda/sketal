import asyncio


class MessageHandler:
    def __init__(self, bot, api, initiate_plugins=True):
        self.bot = bot
        self.api = api

        self.plugins = []

        for plugin in self.bot.settings.PLUGINS:
            plugin.set_up(self.bot, self.api, self)

            self.plugins.append(plugin)

        if initiate_plugins:
            self.initiate_plugins()

    def initiate_plugins(self):
        for plugin in self.plugins:
            plugin.preload()

        for plugin in self.plugins:
            plugin.initiate()

    async def process(self, msg):
        for plugin in self.plugins:
            if await plugin.global_before_message_checks(msg) is False:
                return

        plugins_to_check = msg.reserved_by if msg.reserved_by else self.plugins

        for plugin in plugins_to_check:
            if await plugin.check_message(msg):
                if await self.process_with_plugin(msg, plugin) is not False:
                    return

    async def process_with_plugin(self, msg, plugin):
        for p in self.plugins:
            if await p.global_before_message(msg, plugin) is False:
                return

        result = await plugin.process_message(msg)

        for p in self.plugins:
            await p.global_after_message(msg, plugin, result)

        return result

    async def process_event(self, evnt):
        for plugin in self.plugins:
            if await plugin.global_before_event_checks(evnt) is False:
                return

        plugins_to_check = evnt.reserved_by if evnt.reserved_by else self.plugins

        for plugin in plugins_to_check:
            if await plugin.check_event(evnt):
                if await self.process_event_with_plugin(evnt, plugin) is not False:
                    break

    async def process_event_with_plugin(self, evnt, plugin):
        for p in self.plugins:
            if await p.global_before_event(evnt, plugin) is False:
                return

        result = await plugin.process_event(evnt)

        for p in self.plugins:
            await p.global_after_event(evnt, plugin, result)

        return result

    def stop(self):
        for plugin in self.plugins:
            plugin.stop()
