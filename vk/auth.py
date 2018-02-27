import aiohttp

import json, re
import requests, logging

from urllib.parse import urlparse, parse_qsl


class AuthFallback:
    __slots__ = ("logger", "cli")

    def __init__(self, cli, logger=None):
        self.logger = logger
        self.cli = cli

    async def get_token(self, username, password, appid, scope):
        url = "https://oauth.vk.com/token?grant_type=password&client_id=2274003&client_secret=hHbZxrka2uZ6jB1inYsH&username={username}&password={password}"
        res = json.loads(requests.get(url.format(username=username, password=password)).text)
        token = res.get("access_token")

        if not token:
            return None

        if "user_id" in res:
            if hasattr(self.cli, "user_id"):
                self.cli.user_id = res["user_id"]

        return token


class Auth:
    def __init__(self, obj, logger=None):
        if logger:
            self.logger = logger
        else:
            self.logger = logging.Logger("vk.auth")

        self.obj = obj

    def enter_captcha(self, captcha_url, session=None):
        self.logger.warning('(this can be caused by wrong login/password!)')
        return self.obj.enter_captcha(captcha_url, session)

    def enter_confirmation_code(self):
        return self.obj.enter_confirmation_code()

    @staticmethod
    def get_form_action(html):
        form_action = re.findall(r'<form(?= ).* action="(.+)"', html)
        if form_action:
            return form_action[0]

    @staticmethod
    def get_token_from_url(url):
        if not isinstance(url, str):
            url = str(url)

        url = url.split("access_token=")

        if len(url) < 2:
            return None

        url = url[1].split("&")

        return url[0]

    def get_url_query(self, url):
        if not isinstance(url, str):
            url = str(url)

        parsed_url = urlparse(url)
        url_query = parse_qsl(parsed_url.fragment or parsed_url.query)

        # login_response_url_query can have multiple key
        url_query = dict(url_query)

        token = self.get_token_from_url(url)
        if token:
            url_query["access_token"] = token

        return url_query

    ############################################################################
    async def auth_check_is_needed(self, html, session):
        auth_check_form_action = self.get_form_action(html)
        auth_check_code = await self.enter_confirmation_code()

        auth_check_data = {
            'code': auth_check_code,
            'remember': '1'
        }

        async with session.post(auth_check_form_action, data=auth_check_data) as resp:
            await resp.text()

    async def auth_captcha_is_needed(self, response, login_form_data, captcha_url, session):
        response_url_dict = self.get_url_query(response.url)

        captcha_form_action = self.get_form_action((await response.text()))
        if not captcha_form_action:
            self.logger.error('Cannot find form url in captcha')
            exit()

        captcha_url = '%s?s=%s&sid=%s' % (captcha_url, response_url_dict['s'], response_url_dict['sid'])

        login_form_data['captcha_sid'] = response_url_dict['sid']
        login_form_data['captcha_key'] = await self.enter_captcha(captcha_url, session)

        async with session.post(captcha_form_action, data=login_form_data) as resp:
            await resp.text()

    #############################################################################
    async def get_token(self, username, password, app_id, scope):
        url_get_token = "https://oauth.vk.com/authorize"

        async with aiohttp.ClientSession() as session:
            await self.login(username, password, session)

            token_data = {
                "client_id": app_id,
                "redirect_uri": "https://oauth.vk.com/blank.html?",
                "response_type": "token",
                "scope": scope,
                "display": "mobile",
                "v": 5.67
            }

            headers = {
                "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/58.0.3029.110 Safari/537.36",
                "accept-language": "ru-RU,ru;q=0.8,en-US;q=0.6,en;q=0.4",
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
            }

            async with session.post(url_get_token, data=token_data, headers=headers) as resp:
                html = await resp.text()

                response_url_query1 = self.get_url_query(resp.url)

                if resp.history:
                    response_url_query2 = self.get_url_query(resp.history[-1].headers["Location"])
                else:
                    response_url_query2 = {}

                if 'access_token' in response_url_query1:
                    return response_url_query1['access_token']

                elif 'access_token' in response_url_query2:
                    return response_url_query2['access_token']

                else:
                    form_action = self.get_form_action(html)

            if form_action:
                async with session.post(form_action, headers=headers) as resp:
                    await resp.text()

                    response_url_query1 = self.get_url_query(resp.url)

                    if resp.history:
                        response_url_query2 = self.get_url_query(resp.history[-1].headers["Location"])
                    else:
                        response_url_query2 = {}

                    if 'access_token' in response_url_query1:
                        return response_url_query1['access_token']

                    elif 'access_token' in response_url_query2:
                        return response_url_query2['access_token']

            fallback = AuthFallback(self.obj, self.logger)

            return await fallback.get_token(username, password, app_id, scope)

    async def login(self, username, password, session):
        captcha_url = 'https://m.vk.com/captcha.php'
        url_login = "https://m.vk.com"

        login_form_data = {
            'email': username,
            'pass': password,
        }

        async with session.get(url_login) as resp:
            html = await resp.text()

            login_form_action = self.get_form_action(html)

        if not login_form_action:
            self.logger.error("VK changed authentication flow")
            exit()

        async with session.post(login_form_action, data=login_form_data) as resp:
            await resp.text()

            response_url_query = self.get_url_query(resp.url)

            cookies = [cookie.key for cookie in session.cookie_jar]

            if 'remixsid' in cookies or 'remixsid6' in cookies:
                return

            if 'sid' in response_url_query:
                await self.auth_captcha_is_needed(resp, login_form_data, captcha_url, session)

            elif response_url_query.get('act') == 'authcheck':
                await self.auth_check_is_needed(await resp.text(), session)

            elif 'security_check' in response_url_query:
                self.logger.error("Phone number is needed")

            else:
                self.logger.error("Authorization error (incorrect password)")
