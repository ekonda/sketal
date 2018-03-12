from handler.base_plugin_command import CommandPlugin

import aiohttp, json, time


class EmotionsDetectorPlugin(CommandPlugin):
    __slots__ = ("key", "dirt", "clean_time", "requests_amount", "time_delta")

    def __init__(self, *commands, prefixes=None, strict=False, key=None, time_delta=60, requests_amount=15):
        """Answers with results of detecting emotions on sent image"""

        if not key:
            raise AttributeError("You didn't specified key! You can get it here: https://azure.microsoft.com/ru-ru/services/cognitive-services/face/")

        super().__init__(*commands, prefixes=prefixes, strict=strict)

        self.key = key

        self.dirt = 0
        self.time_delta = time_delta
        self.clean_time = time.time() + time_delta
        self.requests_amount = requests_amount

        example = self.command_example()
        self.description = [f"Детектор эмоций",
                            f"{example} - распознать эмоции на лице'."]

    async def process_message(self, msg):
        if self.dirt >= self.requests_amount:
            if time.time() >= self.clean_time:
                self.dirt = 0
                self.clean_time = time.time() + self.time_delta
            else:
                return await msg.answer('Лимит запросов исчерпан! Попробуйте через минуту или две.')

        photo = False
        for k, v in msg.brief_attaches.items():
            if '_type' in k and v == "photo":
                photo = True
                break

        if not photo:
            return await msg.answer('Вы не прислали фото!')

        attach = (await msg.get_full_attaches())[0]

        if not attach.url:
            return await msg.answer('Вы не прислали фото!')

        uri_base = 'https://westcentralus.api.cognitive.microsoft.com'

        # Request headers.
        headers = {'Content-Type': 'application/json', 'Ocp-Apim-Subscription-Key': self.key}
        params = {'returnFaceId': 'true', 'returnFaceLandmarks': 'false', 'returnFaceAttributes': 'age,gender,emotion'}
        body = {'url': attach.url}

        try:  # Execute the REST API call and get the response.
            self.dirt += 1

            async with aiohttp.ClientSession() as sess:
                async with sess.post(uri_base + '/face/v1.0/detect', data=None, json=body, headers=headers, params=params) as resp:
                    response = await resp.text()
                    parsed = json.loads(response)

                    answer = ""

                    for i, e in enumerate(parsed):
                        age = e["faceAttributes"]["age"]
                        sex = "женский" if e["faceAttributes"]['gender'] == "female" else "мужской"

                        fear = e["faceAttributes"]["emotion"]["fear"]
                        anger = e["faceAttributes"]["emotion"]["anger"]
                        contempt = e["faceAttributes"]["emotion"]["contempt"]
                        disgust = e["faceAttributes"]["emotion"]["disgust"]
                        happiness = e["faceAttributes"]["emotion"]["happiness"]
                        neutral = e["faceAttributes"]["emotion"]["neutral"]
                        sadness = e["faceAttributes"]["emotion"]["sadness"]
                        surprise = e["faceAttributes"]["emotion"]["surprise"]

                        answer += f"Анализ фотографии (лицо #{i + 1})\n💁‍♂️Возраст: {age}\n👫Пол: {sex}\n😵Страх: {fear}\n😤Злость: {anger}\n" \
                                  f"😐Презрение: {contempt}\n🤢Отвращение: {disgust}\n🙂Счастье: {happiness}\n" \
                                  f"😶Нейтральность: {neutral}\n😔Грусть: {sadness}\n😯Удивление: {surprise}\n\n"

                    if not answer:
                        raise ValueError("No answer")

                    return await msg.answer(answer)

        except TypeError:
            return await msg.answer(chat_id=msg.chat_id, message="Ошибочка! Наверное, мой ключ доступа перестал работать.")

        except ValueError:
            pass

        except Exception as e:
            import traceback
            traceback.print_exc()

        await msg.answer(chat_id=msg.chat_id, message="Не удалось обнаружить лицо на фотографии")
