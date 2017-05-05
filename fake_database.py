users = {}


class PuppetUser:
    __slots__ = ("message_date", "uid")

    def __init__(self):
        self.uid = 0
        self.message_date = 0


class Puppet:
    async def create(self, model, **kwargs):
        if "uid" not in kwargs:
            return None

        u = PuppetUser()
        u.uid = kwargs["uid"]
        u.message_date = 0

        users[u.uid] = u

    async def update(self, user):
        users[user.uid] = user

async def get_or_none(model, *args, **kwargs):
    if kwargs["uid"] in users:
        return users[kwargs["uid"]]

    return None

db = Puppet()
