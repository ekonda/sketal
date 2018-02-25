from handler.base_plugin_command import CommandPlugin
import random


class RandomPostPlugin(CommandPlugin):
    __slots__ = ("commgroups", )

    def __init__(self, commgroups, prefixes=None, strict=False):
        """Answers with random post from group specified in commgroups"""

        if not strict:
            self.commgroups = {}

            for k, v in commgroups.items():
                self.commgroups[k.lower()] = v
        else:
            self.commgroups = commgroups

        super().__init__(*list(self.commgroups), prefixes=prefixes, strict=strict)

        self.description = ["Случайные посты из групп", "Доступные команды:"]
        for k in self.commgroups.keys():
            self.description.append(prefixes[0] + str(k))

    async def process_message(self, msg):
        command, text = self.parse_message(msg, full_text=self.strict)
        group_id = self.commgroups[command]

        message, attachments = "", ""

        data = await self.api.wall.get(owner_id=group_id, count=100)

        if not data:
            return await msg.answer("Я не могу получить посты!")

        posts = data["items"]
        count = data["count"]

        if count < 1 or len(posts) < 1:
            return await msg.answer("Не найдено ни одного поста!")

        for _ in range(10):
            if count > 100:
                data = await self.api.wall.get(owner_id=group_id, offset=int(random.random() * (count - 90)), count=100)
                posts = data["items"]

            random.shuffle(posts)

            for i in posts:
                if i.get("marked_as_ads") or i.get("post_type") == "copy":
                    continue

                if i.get("text"):
                    if any(bad in i["text"] for bad in ("vk.com/", "vk.cc/", " подпишись ", "www.", "http://", "https://")):
                        continue

                    message = i["text"]

                for a in i.get("attachments", []):
                    if a["type"] in ("photo", "video", "audio", "doc"):
                        atta = a[a["type"]]

                        attachments += a["type"] + str(atta["owner_id"]) + "_" + str(atta["id"])

                        if "access_key" in atta:
                            attachments += "_" + atta["access_key"]

                        attachments += ","

                if message or attachments:
                    return await msg.answer(message=message, attachment=attachments)

        return await msg.answer("Не найдено ни одного поста!")
