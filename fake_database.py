from database import User

users = {}


class PuppetUser:
    __slots__ = ("message_date", "uid", "chat_data")

    def __init__(self):
        self.uid = 0
        self.message_date = 0
        self.chat_data = ""


class Puppet:
    async def create(self, model, **kwargs):
        if model != User:
            return None

        if "uid" not in kwargs:
            return None

        u = PuppetUser()
        u.uid = kwargs["uid"]
        u.chat_data = ""
        u.message_date = 0

        users[u.uid] = u

    async def update(self, user):
        users[user.uid] = user

async def get_or_none(model, *args, **kwargs):
    if model != User:
        return None

    if kwargs["uid"] in users:
        return users[kwargs["uid"]]

    return None

db = Puppet()
