# Скрипт нужен был для парсинга методов, которые можно выполнять от юзера/сообщества/паблик апи

import requests
from bs4 import BeautifulSoup

URL = "https://vk.com/dev/methods"
BASE_URL = "https://vk.com"
soup = BeautifulSoup(requests.get(URL).content, "html5lib")
DATA = {}
for a in soup.find_all('a', href=True):
    link = a['href']
    if '/dev/' in link and ('.' in link or 'execute' in link):
        REQ_LINK = BASE_URL + link
        html = requests.get(REQ_LINK)
        thing = BeautifulSoup(html.content, "html5lib")
        user = thing.findAll("div",
                             {"class": "dev_method_page_access_row_icon dev_method_page_access_row_open_icon fl_l"})
        if user:
            topic, method = link.replace('/dev/', '').split('.')
            if DATA.get(topic):
                DATA[topic].append(method)
            else:
                DATA[topic] = [method]
            continue
        group = thing.findAll("div", {
            "class": "dev_method_page_access_row_icon dev_method_page_access_row_group_icon fl_l"})
        if group:
            print(link, 'от группы')
        public = thing.findAll("div",
                               {"class": "dev_method_page_access_row_icon dev_method_page_access_row_user_icon fl_l"})
        if public:
            print(link, 'от юзера')

print(DATA)
