import aiohttp
from datetime import date, timedelta
import xml.etree.ElementTree as etree

from plugin_system import Plugin

START_DATE = date.today()

EDU_LOGIN = ''
EDU_PASSWORD = ''
AUTH_DATA = {'main_login': EDU_LOGIN, 'main_password': EDU_PASSWORD}
LOGIN_URL = "https://edu.tatar.ru/logon"
DIARY_URL = "https://edu.tatar.ru/user/diary.xml"
HEADERS = {'Referer': 'https://edu.tatar.ru/logon'}
MONTHS = {
    1: "Январь",
    2: "Февраль",
    3: "Март",
    4: "Апрель",
    5: "Май",
    6: "Июнь",
    7: "Июль",
    8: "Август",
    9: "Сентябрь",
    10: "Октябрь",
    11: "Ноябрь",
    12: "Декабрь"
}
diary = None

plugin = Plugin('Уроки edu.tatar.ru', usage="уроки (число) - просмотреть расписание и задания "
                                            "на сегодня, или на (число)")


async def get_diary():
    async with aiohttp.ClientSession() as sess:
        async with sess.post(LOGIN_URL, headers=HEADERS,
                             data=AUTH_DATA, allow_redirects=False) as resp:
            sess._cookie_jar.update_cookies({"DNSID": resp.cookies['DNSID']})
            async with sess.get(DIARY_URL) as diary:
                async with sess.get(DIARY_URL) as diary:
                    return await diary.text()


def conv(data: str):
    data = data.strip().replace(';', ', ')
    return 'ничего' if not data else data


# Формат - месяц:{числа : ( урок, задание) }
def parse_diary(diary_xml):
    dates = {}
    root = etree.fromstring(diary_xml)
    for page in root:
        month = page.attrib['month']
        if not dates.get(month):
            dates[month] = {}
        for day in page:
            day_num = int(day.attrib['date'])
            classes = [tag.text for tag in day.find('classes').iter('class')]
            tasks = [tag.text for tag in day.find('tasks').iter('task')]
            if not classes or not tasks:
                continue
            dates[month].update({day_num: list(zip(classes, tasks))})

            # data = f'\n{day_num} {month}:\n'
            # data +='\n'.join((cls + " - " + conv(task) for cls, task in zip(classes, tasks) if cls))
    return dates


@plugin.on_command('уроки')
async def test(msg, args):
    when = date.today() + timedelta(days=1)
    if not args:
        day_num = when.day
    elif 'сегодня' in args[0]:
        when = date.today()
        day_num = when.day
    else:
        try:
            # Получаем день и создаём дату с текущими месяцем и годом, но с
            # выбранным днём
            day_num = int(args[0])
            when = date(year=when.year, month=when.month, day=day_num)
        except ValueError:
            # Если человек отправил не число
            return await msg.answer('Введите число!')
    global diary
    if not diary or (when - START_DATE).days > 0:
        # Если в DIARY ничего нет, или разница больше 1 дня
        diary = parse_diary(await get_diary())
    # Получаем текущий месяц из числа
    month = MONTHS[when.month]
    # Получаем информацию в месяце из дневника
    data = diary.get(month)
    if not data:
        return await msg.answer('Не удалось узнать расписание для данного месяца!')
    # Получаем расписание по дню
    sched = data.get(when.day)
    if not sched:
        return await msg.answer('Не удалось узнать расписание для данного дня!')
    result = f'\n{day_num} {month}:\n'
    result += '\n'.join((cls + " - " + conv(task) for cls, task in sched if cls))
    return await msg.answer(result)
