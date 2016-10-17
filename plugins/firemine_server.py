import requests
from plugin_system import Plugin

plugin = Plugin('Онлайн серверов')

message = '''HardTech = {} человек.
TechnoMagic #1 = {} человек.
TechnoMagic #2 = {} человек.
MagicRPG #2 = {} человек.
Общий онлайн = {} человек.
Дневной рекорд = {} человек.
Общий рекорд = {} человек.'''


@plugin.on_command('файнмайн', 'онлайн на файнмайн')
async def get_online(msg, args):
    results = []
    result = requests.get('http://finemine.ru/mon/ajax.php').json()
    for server in ('HardTech', 'TechnoMagic #1', 'TechnoMagic #2', 'MagicRPG'):
        results.append(result['servers'][server]['online'])
    all_servers = result["online"]
    day_record = result["recordday"]
    overall_record = result["record"]
    vk_message = message.format(*results, all_servers, day_record, overall_record)

    await msg.answer(vk_message)
