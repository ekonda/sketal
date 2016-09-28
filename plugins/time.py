import datetime
from plugin_system import Plugin

plugin = Plugin('Время')


@plugin.on_command('время', 'дата', 'тайм', 'сколько время?', 'сколько время', 'сколько времени?')
def get_time(vk, msg, args):
    # Знаю, быдлокод. В идеале нужно брать временную зону Москвы и т.д
    time = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=3)).strftime('%d-%m-%Y %H:%M:%S')
    timemsg = "Текущие дата и время по МСК: "
    vk.respond(msg, {'message': timemsg + '\n' + str(time)})
