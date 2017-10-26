from handler.base_plugin_command import CommandPlugin
import random


class RandomPostPlugin(CommandPlugin):
    __slots__ = ("commgroups", )

    def __init__(self, commgroups, prefixes=None, strict=False):
        """Answers with random post from group specified in commgroups"""

        self.commgroups = commgroups

        super().__init__(*self.commgroups.keys(), prefixes=prefixes, strict=strict)

        self.description = ["Случайные посты из групп", "Доступные команды:"]
        for k, v in self.commgroups.items():
            self.description.append(prefixes[0] + str(k))

    async def process_message(self, msg):
        command, text = self.parse_message(msg)

        post = None
        safe = 5

        group_id = self.commgroups[command]

        while not post and safe > 0:
            safe -= 1

            values = {'owner_id': group_id, 'offset': random.randint(1, 500), 'count': 100}

            posts = await self.api.wall.get(**values)

            if int(posts.get("count", 0)) < 1 and posts.get("items", []):
                return await msg.answer("Не найдено ни одного поста!")

            posts = posts["items"]

            while posts:
                post = posts.pop(random.randint(1, len(posts)))

                text = post.get("text", "")
                if any(t in text for t in ("http://", "https://", "www.", ".ru", "vk.com/")):
                    continue

                atta = ""

                for a in post.get("attachments", []):
                    if a["type"] in ("photo", "video", "music"):
                        atta += a["type"] + str(a[a["type"]]["owner_id"]) + "_" + str(a[a["type"]]["id"]) + \
                                ("_" + a[a["type"]]["access_key"]if "access_key" in a[a["type"]] else "") + ","

                if text or atta:
                    post = text, atta
                    break

        if post is None:
            return await msg.answer("Не найдено ни одного поста!")

        return await msg.answer(message=post[0], attachment=post[1])
