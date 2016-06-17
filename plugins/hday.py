# -*- coding: utf-8 -*-

import os
import sys
import random
import datetime
import operator


class Plugin:
    vk = None
	
    plugin_type = 'command'

    def __init__(self, vk):
        self.vk = vk
        print('Дни рождения')

    def getkeys(self):
        keys = [u'др', u'hd', u'деньрождения']
        ret = {}
        for key in keys:
            ret[key] = self
        return ret

    def call(self, msg):

        # Варианты начала ответа
        answers = []
        answers.append(u"Вот список со днями рождения в группе FineMine.")
        answers.append(u"Список дней рождения в группе FineMine!")
        answers.append(u"Вот твой список именинников, принцесса.")

        # Варианты фразы, назвающей количество участников в группе
        memb_name = []
        memb_name.append(u"Лалочек")
        memb_name.append(u"Участников в группе")
        memb_name.append(u"Человек в группе")

        # Варианты информаци сколько участников указали дату рождения в профиле (и не склрыли её)
        has_bddate = []
        has_bddate.append(u"У стольких указана дата рождения")
        has_bddate.append(u"Указана дата рождения у")
        has_bddate.append(u"Указали дату рождения")

        # Фраза, начинающая список в ответе
        there_list = []
        there_list.append(u"Вот список")
        there_list.append(u"Держи списочек")
        there_list.append(u"Вот эти людишки")
        there_list.append(u"Вот они, эти счастливчики")

        # ID группы, в которой искать
        grp_id = 35140461

        # Первый запрос, что бы получить количество участников группы
        GetMembersRequest = {
        'group_id' : grp_id ,
        'sort' : 'id_asc',
        'offset' : 0,
        'count' : 1
        #'fields' : 'bdate',
        }
        
        members = self.vk.method('groups.getMembers', GetMembersRequest)

        mcnt = members['count']

        # Костыль. Этот метод возвращает не более 1000 записей. По этому пока что на всякий случай стоит ограничитель. 
        # В будущем нужно будет реализовать получение списка несколькими запросами.
        if mcnt > 1000:
            mcnt = 1000

        # Второй запрос. Получает информацию о пользователях сообщества. 
        # Пока что за один раз. 
        GetMembersRequest = {
        'group_id' : grp_id ,
        'sort' : 'id_asc',
        'offset' : 0 ,
        'count' : mcnt , 
        'fields' : 'bdate'
        }       

        members = self.vk.method('groups.getMembers', GetMembersRequest)

        mcnt = members['count']         # Зачем? Но пока оставлю так. Можно же дальше использовать members['count'] или я его буду портить?

        members = members['items']      # Отделяю записи пользователей в список словарей.

        has_bdate = 0     # Счётчик - сколько участников указали дату рождения. На данный момент практического значения не имеет. Просто показатель.
        
        dayshift = 6      # Указывается промежуток в днях от текущей даты, в который должны попадать люди с днём рождения.

        lastdate = datetime.date.today() + datetime.timedelta(dayshift) # Последний день - конец промежутка
        today = datetime.date.today()                                   # Сегодня - начало промежутка 

        mbbday = []       # Список участников, с датой рождения, попадающий в указанный промежуток времени. Обнуляем его.

        # Поиск участников по списку
        for member in members:
            if 'bdate' in member:
                has_bdate += 1
                if len(member['bdate'].split('.')) > 2:
                    mbdate = datetime.datetime.strptime(member['bdate'],'%d.%m.%Y') # Если дата указана с годом
                else:
                    mbdate = datetime.datetime.strptime(member['bdate'],'%d.%m')    # Если дата указана без года

                if ((today.month, today.day) <= (mbdate.month, mbdate.day)) and ((lastdate.month, lastdate.day) >= (mbdate.month, mbdate.day)):
                    member['mbdate'] = mbdate # Добавляем в словарь дату в формате datetime.datetime.strptime для дальнейшей сортировки списка.
                    mbbday.append(member)

        # Очищаем строку списка ответа
        members_list_string = ''

        # Сортируем сначала по месяцам, а потом по дням (внутри месяца).
        # ++ Проверенно! Работает правильно!
        mbbday.sort(key=lambda x: (x['mbdate'].month, x['mbdate'].day))         

        # Создаём строку списка ответа
        for member in mbbday:
            members_list_string += u'\n' + member['bdate'] + u' :: ' + member['first_name'] + u' ' + member['last_name'] + u' => https://vk.com/id' + str(member['id'])

        # Печатаем в "лог" отладочную информацию
        print mcnt
        print has_bdate
        print len(mbbday)

        # Отвечаем в ВК
        self.vk.respond(msg, {'message': random.choice(answers) + u'\n' + random.choice(memb_name) + u': ' + str(mcnt) + u'\n' + random.choice(has_bddate) + u': ' +str(has_bdate) + u'\n Скоро (В ближайшие ' + str(dayshift) + u' дней)  : ' + str(len(mbbday)) + u'\n' + random.choice(there_list) + u':' + members_list_string})
