from handler.base_plugin import BasePlugin

import aiohttp


class DialogflowPlugin(BasePlugin):
    __slots__ = ("prefixes", "client_token", "base_url", "base_version")

    def __init__(self, client_token="6872cbf5cb1c4d1bb63a6fbed8678aff", prefixes=("",)):
        super().__init__()

        self.prefixes = prefixes
        self.client_token = client_token

        self.base_url = "https://api.dialogflow.com/v1/query"
        self.base_version = "20170712"

    async def check_message(self, msg):
        if msg.is_out or msg.is_forwarded:
            return False

        for prefix in self.prefixes:
            if msg.text.startswith(prefix):
                msg.meta["__text_wo_prefix"] = msg.text.replace(prefix, "", 1).strip()
                return True

        return False

    async def process_message(self, msg):
        headers = {
            "Authorization": f"Bearer {self.client_token}",
        }

        body = {
            "lang": "ru",
            "contexts": ["chat"],
            "query": msg.meta["__text_wo_prefix"],
            "sessionId": str(self.api.get_current_id()) + "_" + str(msg.user_id),
        }

        params = {
            "v": self.base_version
        }

        async with aiohttp.ClientSession() as sess:
            async with sess.post(self.base_url, json=body, headers=headers, params=params) as resp:
                resp_json = await resp.json()

        code = resp_json.get("status", {}).get("code")
        if code != 200:
            if code == 429:
                self.api.logger.warning("429 - too_many_requests")

            elif code == 400:
                self.api.logger.warning(str(code) + " - " + resp_json["status"]["errorDetails"])

            return await msg.answer("Простите, я потерялся. Попробуйте позже.")

        text = resp_json.get("result", {}).get("fulfillment", {}).get("speech")
        if not text:
            return await msg.answer("Я не понял.")

        return await msg.answer(text)
