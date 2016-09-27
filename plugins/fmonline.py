
import random
import requests
from plugin_system import Plugin

plugin = Plugin('Онлайн серверов')

@plugin.on_command('файрмайн','онлайнфм')
def get_online(vk, raw_message, args):
    online_hard = requests.get("http://finemine.ru/mon/ajax.php")
    onlineid_hard = online_hard.json()["servers"]["HardTech"]["online"]
    online_tm1 = requests.get("http://finemine.ru/mon/ajax.php")
    onlineid_tm1 = online_tm1.json()["servers"]["TechnoMagic #1"]["online"]
    online_tm2 = requests.get("http://finemine.ru/mon/ajax.php")
    onlineid_tm2 = online_tm2.json()["servers"]["TechnoMagic #2"]["online"]
    online_magic = requests.get("http://finemine.ru/mon/ajax.php")
    onlineid_magic = online_magic.json()["servers"]["MagicRPG"]["online"]
    online_all = requests.get("http://finemine.ru/mon/ajax.php")
    onlineid_all = online_all.json()["online"]
    online_redordday = requests.get("http://finemine.ru/mon/ajax.php")
    onlineid_redordday = online_redordday.json()["recordday"]
    online_redord = requests.get("http://finemine.ru/mon/ajax.php")
    onlineid_redord = online_redord.json()["record"]
    vk_message = "HardTech = {} человек. \n TechnoMagic #1 = {} человек. \n TechnoMagic #2 = {} человек. \n MagicRPG #2 = {} человек. \n Общий онлайн = {} человек. \n Дневной рекорд = {} человек. \n Общий рекорд = {} человек.".format(
        onlineid_hard, onlineid_tm1, onlineid_tm2, onlineid_magic, onlineid_all, onlineid_redordday,
        onlineid_redord)

    vk.respond(raw_message, {'message': vk_message})
