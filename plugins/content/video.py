from handler.base_plugin_command import CommandPlugin

import aiohttp

class VideoPlugin(CommandPlugin):
    __slots__ = ()

    def __init__(self, *commands, prefixes=None, strict=False):
        
        super().__init__(*commands, prefixes=prefixes, strict=strict)
        example = self.command_example()
        self.description = ["Видео", f"{self.command_example()} [запрос] - поиск видео по запросу"]

    async def process_message(self, msg):
        command, text = self.parse_message(msg, full_text=True)
        data = await self.api.video.search(q=text,sort=2,count=10,adult=1)

        if not data:
            return await msg.answer("Я не могу получить видео!")

        vids = data["items"]

        resp = ','.join(f"video{vid['owner_id']}_{vid['id']}" for vid in vids)
    
        if not resp:
            return await msg.answer(f"По запросу {text} ничего не найдено!")

        await msg.answer('Приятного просмотра!', attachment=resp)
