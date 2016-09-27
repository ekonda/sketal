import random
import datetime

from say import say

from plugin_system import Plugin

# Варианты начала ответа.
answers = []
answers.append("Вот список со днями рождения в группе.")
answers.append("Список дней рождения в группе !")
answers.append("Вот твой список именинников.")

# Варианты фразы, назвающей количество участников в группе
memb_name = []
memb_name.append("Лалочек")
memb_name.append("Участников в группе")
memb_name.append("Человек в группе")

# Варианты информации сколько участников указали дату рождения в профиле (и не скрыли её)
has_bddate = []
has_bddate.append("У стольких указана дата рождения")
has_bddate.append("Указана дата рождения у")
has_bddate.append("Указали дату рождения")

# Фраза, начинающая список в ответе
there_list = []
there_list.append("Вот список")
there_list.append("Держи списочек")
there_list.append("Вот эти людишки")
there_list.append("Вот они, эти счастливчики")

plugin = Plugin('Дни рождения')


@plugin.on_command('деньрождения', 'др')
def check(vk, msg, args):
    # ID группы, в которой искать
    if len(args) != 1:
        return

    try:
        grp_id = int(args[0])  # Первый запрос, чтобы получить количество участников группы
        if grp_id < 0:
            vk.respond(msg, {'message': 'Вы ввели отриц. число!'})
            return
    except:
        vk.respond(msg, {'message': 'Вы ввели не число!'})
        return
    GetMembersRequest = {
        'group_id': grp_id,
        'sort': 'id_asc',
        'offset': 0,
        'count': 1
        # 'fields' : 'bdate',
    }

    members = vk.method('groups.getMembers', GetMembersRequest)
    if not members:
        vk.respond(msg, {'message': 'Такой группы не существует, или она только по приглашениям!'})
        return
    mcnt = members['count']

    # Костыль. Этот метод возвращает не более 1000 записей. По этому пока что на всякий случай стоит ограничитель.
    # В будущем нужно будет реализовать получение списка несколькими запросами.
    if mcnt > 1000:
        mcnt = 1000

    # Второй запрос. Получает информацию о пользователях сообщества.
    # Пока что за один раз.
    GetMembersRequest = {
        'group_id': grp_id,
        'sort': 'id_asc',
        'offset': 0,
        'count': mcnt,
        'fields': 'bdate'
    }

    members = vk.method('groups.getMembers', GetMembersRequest)

    mcnt = members[
        'count']  # Зачем? Но пока оставлю так. Можно же дальше использовать members['count'] или я его буду портить?

    members = members['items']  # Отделяю записи пользователей в список словарей.

    has_bdate = 0  # Счётчик - сколько участников указали дату рождения. На данный момент практического значения не имеет. Просто показатель.

    dayshift = 6  # Указывается промежуток в днях от текущей даты, в который должны попадать люди с днём рождения.

    lastdate = datetime.date.today() + datetime.timedelta(dayshift)  # Последний день - конец промежутка
    today = datetime.date.today()  # Сегодня - начало промежутка

    mbbday = []  # Список участников, с датой рождения, попадающий в указанный промежуток времени. Обнуляем его.

    # Поиск участников по списку
    for member in members:
        if 'bdate' in member:
            has_bdate += 1
            if len(member['bdate'].split('.')) > 2:
                mbdate = datetime.datetime.strptime(member['bdate'], '%d.%m.%Y')  # Если дата указана с годом
            else:
                try:
                    mbdate = datetime.datetime.strptime(member['bdate'], '%d.%m')  # Если дата указана без года
                except ValueError:  # Если человек указал дату типа 69.11
                    continue

            if ((today.month, today.day) <= (mbdate.month, mbdate.day)) and (
                        (lastdate.month, lastdate.day) >= (mbdate.month, mbdate.day)):
                member[
                    'mbdate'] = mbdate  # Добавляем в словарь дату в формате datetime.datetime.strptime для дальнейшей сортировки списка.
                mbbday.append(member)

    # Очищаем строку списка ответа
    members_list_string = ''

    # Сортируем сначала по месяцам, а потом по дням (внутри месяца).
    mbbday.sort(key=lambda x: (x['mbdate'].month, x['mbdate'].day))

    # Создаём строку списка ответа
    for member in mbbday:
        members_list_string += '\n' + member['bdate'] + ' :: ' + member['first_name'] + ' ' + member[
            'last_name'] + ' => https://vk.com/id' + str(member['id'])

    # Печатаем в лог отладочную информацию
    say("Кол-во участников получено {mcnt}, из них у {has_bdate} есть дата рождения, у {len(mbbday)} скоро ДР.")

    # Отвечаем в ВК
    vk.respond(msg, {'message': random.choice(answers) + '\n' + random.choice(memb_name) + ': ' + str(
        mcnt) + '\n' + random.choice(has_bddate) + ': ' + str(has_bdate) + '\n Скоро (В ближайшие ' + str(
        dayshift) + ' дней)  : ' + str(len(mbbday)) + '\n' + random.choice(
        there_list) + ':' + members_list_string})
