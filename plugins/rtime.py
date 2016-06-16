# -*- coding: utf-8 -*-

import random
import pytz
import datetime


class Plugin:
    global timeM
    global timeK
    vk = None
    tzm = pytz.timezone('Europe/Moscow')
    timeM = datetime.datetime.now(tzm).strftime('%d-%m-%Y %H:%M')

    def __init__(self, vk):
        self.vk = vk
        print('Время')

    def getkeys(self):
        keys = [u'время', u'time', u'rtime', u'дата', u'date']
        ret = {}
        for key in keys:
            ret[key] = self
        return ret

    def call(self, msg):
        timemsg = "Текущее дата и время: "
        self.vk.respond(msg, {'message': timemsg + '\n' + str(timeM)})
