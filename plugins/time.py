
import datetime
from plugin_system import Plugin

plugin = Plugin('Время')

# Знаю, быдлокод. В идеале нужно брать временную зону Москвы и т.д
timeM = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=3)).strftime('%d-%m-%Y %H:%M')

@plugin.on_command('время', 'дата', 'тайм')
def get_time(vk, msg, args):
    timemsg = "Текущие дата и время по МСК: "
    vk.respond(msg, {'message': timemsg + '\n' + str(timeM)})
