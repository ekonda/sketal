from enum import Enum
import asyncio

from constants import MAX_LENGHT


class Wait(Enum):
    NO = 0
    YES = 1
    CUSTOM = 2


class EventType(Enum):
    Longpoll = 0
    ChatChange = 1
    Callback = 2


class ProxyParametrs:
    __slots__ = ("parent", "wait", "sender")

    def __init__(self, parent, sender=None, wait=Wait.YES):
        self.sender = sender
        self.wait = wait
        self.parent = parent

    def __getattr__(self, outer_name):
        return self.parent.create_proxy(outer_name, self.sender, self.wait)


class Proxy:
    __slots__ = ("parent", "outer_name",
                 "wait", "sender")

    def __init__(self, parent, outer_name, sender=None, wait=Wait.YES):
        self.parent = parent
        self.outer_name = outer_name

        self.wait = wait
        self.sender = sender

    def __getattr__(self, inner_name):
        async def wrapper(**data):
            return await self.parent.method(f"{self.outer_name}.{inner_name}", data, sender=self.sender, wait=self.wait)

        return wrapper


class Request(asyncio.Future):
    __slots__ = ("key", "data", "sender", "time")

    def __init__(self, key, data, sender=None):
        self.key = key
        self.data = data
        self.sender = sender

        super().__init__()


class RequestAccumulative(Request):
    __slots__ = ("join_func", "results")

    def __init__(self, key, data, sender=None, join_func=None):
        super().__init__(key, data, sender)

        self.results = []

        if join_func:
            self.join_func = join_func

        else:
            self.join_func = lambda x, y: ",".join([x, y]) if x else y

    def accumulate(self, data, amount=1):
        for ok, ov in data.items():
            if ok not in self.data:
                continue

            if ov in self.data[ok]:
                continue

            self.data[ok] = self.join_func(self.data[ok], ov)

        future = asyncio.Future()
        future.requests_amount = amount
        self.results.append(future)

        return future

    def process_result(self, result):
        for t in self.results:
            if t.done() or t.cancelled():
                continue

            try:
                t.set_result(result.pop(0))

            except (KeyError, IndexError, AttributeError):
                t.set_result(False)

            except asyncio.InvalidStateError:
                continue


class Sender:
    __slots__ = ('target', 'user', 'group')

    def __init__(self, target=None, user=False, group=False):
        if not (user or group):
            raise ValueError("Atleast one of argumebts `user` or `group` should be set to True")

        self.user = user
        self.group = group
        self.target = target


class MessageBuilder:
    __slots__ = ("messages", "messages_lengths", "texts", "texts_lengths")

    def __init__(self):
        self.messages = [""]
        self.messages_lengths = [0]

        self.texts = []
        self.texts_lengths = []

    def append(self, text):
        self.texts.append(text)
        self.texts_lengths.append(len(text))

    def append_divider(self):
        current_length = sum(self.texts_lengths)

        if self.messages[-1] and current_length + self.messages_lengths[-1] > MAX_LENGHT:
            self.messages_lengths.append(current_length)
            self.messages.append("".join(self.texts))

        else:
            self.messages_lengths[-1] += current_length
            self.messages[-1] += "".join(self.texts)

        self.texts = []
        self.texts_lengths = []

    def result(self):
        if self.texts:
            self.append_divider()

        for m in self.messages:
            yield m


class Attachment(object):
    __slots__ = ('type', 'owner_id', 'id', 'access_key', 'url')

    def __init__(self, attach_type, owner_id, aid, access_key, url):
        self.type = attach_type
        self.owner_id = owner_id
        self.id = aid
        self.access_key = access_key
        self.url = url

    @staticmethod
    def from_upload_result(result, attach_type="photo"):
        url = ""

        for k in result:
            if "photo_" in k:
                url = result[k]

            elif "link_" in k:
                url = result[k]

            elif "url" in k:
                url = result[k]

        return Attachment(attach_type, result["owner_id"], result["id"], "", url)

    @staticmethod
    def from_raw(raw_attach):
        a_type = raw_attach['type']  # Тип аттача
        attach = raw_attach[a_type]  # Получаем сам аттач

        url = ""
        for k, v in attach.items():  # Ищём ссылку на фото
            if "photo_" in k:
                url = v

        key = attach.get('access_key')  # Получаем access_key для аттача

        return Attachment(a_type, attach.get('owner_id', ''), attach.get('id', ''), key, url)

    def value(self):
        if self.access_key:
            return f'{self.type}{self.owner_id}_{self.id}_{self.access_key}'

        return f'{self.type}{self.owner_id}_{self.id}'

    def __str__(self):
        return self.value()


class MessageEventData(object):
    __slots__ = ('is_multichat', 'user_id', 'full_text', "full_message_data",
                 'time', "msg_id", "attaches", "is_out", "forwarded", "chat_id",
                 'true_user_id')

    @staticmethod
    def from_message_body(obj):
        data = MessageEventData()

        data.attaches = {}
        data.forwarded = []

        c = 0
        for a in obj.get("attachments", []):
            c += 1

            data.attaches[f'attach{c}_type'] = a['type']
            data.attaches[f'attach{c}'] = f'{a[a["type"]]["owner_id"]}_{a[a["type"]]["id"]}'

        if 'fwd_messages' in obj:
            data.forwarded = MessageEventData.parse_brief_forwarded_messages(obj)

        if "chat_id" in obj:
            data.is_multichat = True
            data.chat_id = int(obj["chat_id"])

        if "id" in obj:
            data.msg_id = obj["id"]

        data.user_id = int(obj['user_id'])
        data.true_user_id = int(obj['user_id'])
        data.full_text = obj['body']
        data.time = int(obj['date'])
        data.is_out = obj.get('out', False)
        data.full_message_data = obj

        return data

    @staticmethod
    def parse_brief_forwarded_messages(obj):
        if 'fwd_messages' not in obj:
            return ()

        result = []

        for mes in obj['fwd_messages']:
            result.append((mes.get('id', None), MessageEventData.parse_brief_forwarded_messages(mes)))

        return tuple(result)

    @staticmethod
    def parse_brief_forwarded_messages_from_lp(data):
        result = []

        token = ""
        i = -1
        while True:
            i += 1

            if i >= len(data):
                if token:
                    result.append((token, ()))

                break

            if data[i] in "1234567890_-":
                token += data[i]
                continue

            if data[i] in (",", ")"):
                if not token:
                    continue

                result.append((token, ()))
                token = ""
                continue

            if data[i] == ":":
                stack = 1

                for j in range(i + 2, len(data)):
                    if data[j] == "(":
                        stack += 1

                    elif data[j] == ")":
                        stack -= 1

                    if stack == 0:
                        jump_to_i = j
                        break

                sub_data = data[i + 2: jump_to_i]

                result.append((token, MessageEventData.parse_brief_forwarded_messages_from_lp(sub_data)))

                i = jump_to_i + 1
                token = ""
                continue

        return tuple(result)

    def __init__(self):
        self.is_multichat = False
        self.is_out = False

        self.chat_id = 0
        self.user_id = 0
        self.true_user_id = 0
        self.full_text = ""
        self.time = ""
        self.msg_id = 0
        self.attaches = None
        self.forwarded = None
        self.full_message_data = None
