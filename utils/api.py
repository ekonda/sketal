import asyncio, json, logging, time

import aiohttp

from .auth import Auth
from .utils import RequestAccumulative
from .routine import json_iter_parse

AUTHORIZATION_FAILED = 5
CAPTCHA_IS_NEEDED = 14
ACCESS_DENIED = 15
INTERNAL_ERROR = 10
EXECUTE_ERROR = 10000
VERSION = "5.68"

class VkClient:
    """Class for organazing, controlling and processing requests to vk from group or user."""

    __slots__ = ("token", "session", "req_kwargs", "auth",
                 "username", "password", "app_id", "scope",
                 "solver", "logger", "group_id", "user_id",
                 "queue", "loop")

    def __init__(self, solver=None, proxy=None, logger=None, loop=None):
        if logger:
            self.logger = logger
        else:
            self.logger = logging.Logger("vk_client")

        if loop:
            self.loop = loop
        else:
            self.loop = asyncio.get_event_loop()

        self.solver = solver
        self.auth = Auth(self, logger=self.logger)

        self.req_kwargs = {}
        if proxy:
            url, username, password, encoding = *proxy, None, None, None

            self.req_kwargs["proxy"] = url

            if username:
                self.req_kwargs["proxy_auth"] = aiohttp.BasicAuth(username,
                                                                  password if password else "",
                                                                  encoding if encoding else "latin1")

        self.session = aiohttp.ClientSession()

        self.queue = RequestsQueue(self, logger=self.logger)

        self.username = ""
        self.password = ""
        self.app_id = None
        self.scope = None

        self.group_id = 0
        self.user_id = 0

        self.token = ""

    def __str__(self):
        return f"Group ({self.group_id})" if self.group_id else f"User ({self.user_id})"

    async def method(self, key, **data):
        "Return a result of executing vk's method `method`. Function for \
        special cases only! This method doesn't process nor errors nor captcha."

        url = f"https://api.vk.com/method/{key}?access_token={self.token}&v={VERSION}"

        if data is None:
            data = {}

        nl_to_text = data.pop("_nl_to_text", False)
        nl_to_br = not nl_to_text and data.pop("_nl_to_br", True)

        if nl_to_br:
            for k, v in data.items():
                if isinstance(v, str):
                     data[k] = v.replace("\r\n", "<br>").replace("\n", "<br>")

        if nl_to_text:
            for k, v in data.items():
                if isinstance(v, str):
                     data[k] = v.replace("\n", "\\n")

        async with self.session.post(url, data=data, **self.req_kwargs) as resp:
            try:
                results = json_iter_parse(await resp.text())

                for data in results:
                    if 'response' in data:
                        return data['response']

            except json.JSONDecodeError:
                self.logger.error("Error while executing vk method: vk's response is wrong!")

                return {}

        return {}

    async def execute(self, code, **additional_values):
        """Execute a `code` from vk's `execute` method"""

        async with self.session.post(f"https://api.vk.com/method/execute",
                data={"code": code, "access_token": self.token, "v": VERSION,
                **additional_values}, **self.req_kwargs) as resp:
            try:
                response = await resp.text()

                self.logger.debug(f"Request with code:\n{code}\nResponse:\n{response}")

                results = json_iter_parse(response)

            except json.JSONDecodeError:
                self.logger.error("Error while executing vk method: vk's response is wrong!")
                return {}

        errors = []

        for data in results:
            if 'error' in data:
                if data['error']['error_code'] == CAPTCHA_IS_NEEDED:
                    captcha_key = await self.enter_captcha(data['error']["captcha_img"])

                    if not captcha_key:
                        return {}

                    return await self.execute(code, captcha_key=captcha_key,
                        captcha_sid=data['error']["captcha_sid"], **additional_values)

                errors.append(data['error'])

            if 'execute_errors' in data:
                for error in data['execute_errors']:
                    errors.append({
                        'error_code': error['error_code'],
                        'method': error['method'],
                        'error_msg': error['error_msg']
                    })

                continue

            if 'response' in data:
                return data['response']

        if any(error['error_code'] == INTERNAL_ERROR for error in errors):
            return {}

        if any(error['error_code'] == AUTHORIZATION_FAILED for error in errors):
            if self.app_id:
                await self.user(self.username, self.password, self.app_id, self.scope)
                return await self.execute(code)

        error_text = ""
        for error in errors:
            error_text += (str(error)) + "\n"

        self.logger.error("Errors while executing vk method:\n" + error_text[:-1])

        return {}

    async def user_with_token(self, token):
        """Authorize a user by his token"""

        self.token = token

        self_data = await self.method("account.getProfileInfo")

        if not isinstance(self_data, dict):
            return

        my_user = await self.method("users.get")

        if isinstance(my_user, list) and my_user:
            my_user = my_user[0]

        if isinstance(my_user, dict):
            self.user_id = my_user.get("id", 0)

        self.logger.info(f"Logged in as: {self_data['first_name']} {self_data['last_name']} "
                         f"(https://vk.com/id{self.user_id})")

    async def user(self, username, password, app_id, scope):
        """Authorize a user by his username and password"""

        self.username = username
        self.password = password
        self.app_id = app_id
        self.scope = scope

        retries = 5
        for _ in range(retries):
            self.token = await self.auth.get_token(username, password, app_id, scope)

            if self.token:
                break

        if not self.token:
            return self.logger.error("Can't get token!")

        await self.user_with_token(self.token)

    async def group(self, token):
        """Authorize a group by it's token"""

        self.token = token

        self_data = await self.method("groups.getById")

        if not isinstance(self_data, (dict, list)):
            return

        self_data = self_data[0]

        self.group_id = self_data['id']

        address = "https://vk.com/"

        if not self_data.get('screen_name'):
            address += "public" + str(self.group_id) + " *possibly"

        else:
            address += self_data.get('screen_name')

        self.logger.info(f"Logged in as: {self_data['name']} ({address})")

    async def enter_captcha(self, url, session=None):
        """Process captcha image on `url`"""

        if session is None:
            session = self.session

        if not self.solver:
            self.logger.warning("Enter information for captcha solving in settings.py")

            async with session.get(url) as resp:
                with open("captcha.png", "wb") as o:
                    o.write(await resp.read())

            return input("Enter captcha from file `captcha.png`: ")

        try:
            async with session.get(url) as resp:
                img_data = await resp.read()
                data = self.solver.solve_captcha(img_data)
                return data
        except Exception as e:
            self.logger.error(e)

    @staticmethod
    async def enter_confirmation_code():
        """Helper method for logging into account with double-factor authentication"""

        print("Looks like you have two-factor authorization enabled!")
        print("Please, enter your confirmation code:")

        code = input()

        print("Thanks! Continue working....")

        return code

    async def stop(self):
        """Method for cleaning"""

        await self.session.close()


class RequestsQueue:
    __slots__ = ("vk_client", "queue", "requests_done_clear_time",
                 "_requests_done", "processor", "logger")

    def __init__(self, vk_client, logger=None):
        if logger:
            self.logger = logger
        else:
            self.logger = logging.Logger("vk_reqque")

        self.vk_client = vk_client

        self.processor = asyncio.ensure_future(self.queue_processor())

        self._requests_done = 0
        self.requests_done_clear_time = 0

        self.queue = asyncio.Queue()

    def get_nowait(self):
        return self.queue.get_nowait()

    def put_nowait(self, data):
        return self.queue.put_nowait(data)

    @property
    def requests(self):
        return self.queue.qsize()

    @property
    def requests_done(self):
        if self.requests_done_clear_time < time.time():
            self._requests_done = 0
            self.requests_done_clear_time = time.time() + 1

        return self._requests_done

    async def queue_processor(self):
        while True:
            try:
                await self._queue_processor()
            except Exception:
                import traceback
                traceback.print_exc()

            if not self.requests:
                await asyncio.sleep(0.44)

            await asyncio.sleep(0.34)

    async def _queue_processor(self):
        """Process queue"""

        if not self.requests:
            return

        if self.requests_done > 2:
            return await asyncio.sleep(
                max(0, self.requests_done_clear_time - time.time())
            )

        await self.execute_queue()

    async def enqueue(self, task):
        """Add task to client's queue and update queue processor"""
        if not task:
            return False

        self.queue.put_nowait(task)

        return task

    async def execute_queue(self):
        """Execute 25 or less tasks from client's queue"""

        if not self.requests or self.requests_done > 2:
            return

        current_tasks = []

        execute_code = "return ["

        for _ in range(25):
            if self.queue.empty():
                break

            task = self.queue.get_nowait()

            if task.key in ("photos.saveWallPhoto", "messages.setChatPhoto",):
                self._requests_done += 1

                try:
                    result = await self.vk_client.method(task.key, **task.data)
                except Exception:
                    import traceback
                    traceback.print_exc()

                if not task.done() and not task.cancelled():
                    task.set_result(result or {})

                return

            execute_code += "API." + task.key + "({ "

            nl_to_text = task.data.pop("_nl_to_text", False)
            nl_to_br = not nl_to_text and task.data.pop("_nl_to_br", True)

            nl_to_text = task.data.pop("_nl_to_text", False)
            nl_to_br = not nl_to_text and task.data.pop("_nl_to_br", True)

            for k, v in task.data.items():
                if isinstance(v, (int, float)):
                    execute_code += '"' + str(k) + '":' + str(v) + ','
                    continue

                if not isinstance(v, str):
                    v = str(v)

                if nl_to_br:
                    v = v.replace("\n", "<br>")

                v = v.replace('\\', '\\\\').replace('"', '\\"')

                if nl_to_text:
                    v = v.replace("\n", "\\n")

                execute_code += '"' + str(k) + '":"' + v + '",'

            execute_code = execute_code[:-1] + '}),'

            current_tasks.append(task)

        execute_code = execute_code[:-1] + "];"

        result = []

        for _ in range(2):
            self._requests_done += 1

            try:
                result = await self.vk_client.execute(execute_code)

            except aiohttp.ClientOSError:
                await self.vk_client.close()
                self.vk_client.session = aiohttp.ClientSession()

            except Exception:
                import traceback
                traceback.print_exc()

                await asyncio.sleep(0.25)

            else:
                break

        for task in current_tasks:
            if task.done() or task.cancelled():
                continue

            try:
                task_result = result.pop(0)
            except (KeyError, IndexError, AttributeError):
                task_result = {}

            if isinstance(task, RequestAccumulative):
                task.process_result(task_result)
            else:
                try:
                    task.set_result(task_result)
                except asyncio.InvalidStateError:
                    pass
