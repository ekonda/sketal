import datetime
import random

from plugin_system import Plugin

# Варианты начала ответа.
answers = '''Вот список со днями рождения в группе.
Список дней рождения в группе!
Вот твой список именинников.
'''.splitlines()

# Варианты фразы, называющей количество участников в группе
memb_name = '''Лалочек
Участников в группе
Человек в группе
'''.splitlines()

# Варианты информации сколько участников указали дату рождения в профиле (и не скрыли её)
has_bddate = '''У стольких указана дата рождения (из тысячи)
Указана дата рождения у (из тысячи)
Указали дату рождения (из тысячи)
'''.splitlines()

# Фраза, начинающая список в ответе
there_list = '''Вот список
Держи списочек
Вот эти людишки
Вот они, эти счастливчики
'''.splitlines()

plugin = Plugin('Дни рождения в группе', usage="др - узнать дни рождения в группе")


# TODO: Отрефакторить эту херню
@plugin.on_command('др')
async def check(msg, args):
    # ID группы, в которой искать
    if not args:
        return

    try:
        possible_id = args[0]
        # Пытаемся получить ID группы по короткому имени
        grp_id = await msg.vk.resolve_name(possible_id)
        # Если не получилось, конвертируем аргумент в число
        if not grp_id:
            grp_id = abs(int(possible_id))
        if not grp_id:
            return
    except ValueError:
        return await msg.answer('Вы ввели не число!')

    get_members_request = {
        'group_id': grp_id,
        'sort': 'id_asc',
        'offset': 0,
        'count': 1
        # 'fields' : 'bdate',
    }

    members = await msg.vk.method('groups.getMembers', get_members_request)
    if not members:
        await msg.answer('Такой группы не существует, или же она частная!')
        return
    mcnt = members['count']

    # Костыль. Этот метод возвращает не более 1000 записей. 
    # Поэтому пока что на всякий случай стоит ограничитель.
    # В будущем нужно будет реализовать получение списка несколькими запросами.
    if mcnt > 1000:
        mcnt = 1000

    # Второй запрос. Получает информацию о пользователях сообщества.
    # Пока что за один раз.
    get_members_request = {
        'group_id': grp_id,
        'sort': 'id_asc',
        'offset': 0,
        'count': mcnt,
        'fields': 'bdate'
    }

    members = await msg.vk.method('groups.getMembers', get_members_request)

    mcnt = members[
        'count']  # Зачем? Но пока оставлю так. Можно же дальше использовать members['count'] или я его буду портить?

    members = members['items']  # Отделяю записи пользователей в список словарей.

    has_bdate = 0  # Счётчик - сколько участников указали дату рождения. 
    # На данный момент практического значения не имеет. Просто показатель.

    dayshift = 6  # Указывается промежуток в днях от текущей даты, 
    # в который должны попадать люди с днём рождения.

    lastdate = datetime.date.today() + datetime.timedelta(dayshift)  # Последний день - конец промежутка
    today = datetime.date.today()  # Сегодня - начало промежутка

    mbbday = []  # Список участников, с датой рождения, 
    # попадающий в указанный промежуток времени. Обнуляем его.

    # Поиск участников по списку
    for member in members:
        if 'bdate' not in member:
            continue
        has_bdate += 1
        if len(member['bdate'].split('.')) > 2:
            mbdate = datetime.datetime.strptime(member['bdate'], '%d.%m.%Y')  # Если дата указана с годом
        else:
            try:
                mbdate = datetime.datetime.strptime(member['bdate'], '%d.%m')  # Если дата указана без года
            except ValueError:  # Если человек указал дату типа 69.11
                continue

        if ((today.month, today.day) <= (mbdate.month, mbdate.day)) and \
                ((lastdate.month, lastdate.day) >= (mbdate.month, mbdate.day)):
            member['mbdate'] = mbdate
            # Добавляем в словарь дату в формате datetime.datetime.strptime 
            # для дальнейшей сортировки списка.
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
    print("Кол-во участников получено {}, из них у {} есть дата рождения, у {} скоро ДР.".format(
        mcnt, has_bdate, len(mbbday)
    ))

    # Отвечаем в ВК
    await msg.answer(random.choice(answers) + '\n' + random.choice(memb_name) + ': ' + str(
        mcnt) + '\n' + random.choice(has_bddate) + ': ' + str(has_bdate) + '\n Скоро (В ближайшие ' + str(
        dayshift) + ' дней)  : ' + str(len(mbbday)) + '\n' + random.choice(
        there_list) + ':' + members_list_string)
