import datetime
from plugin_system import Plugin

plugin = Plugin('Время')

days = {
    0: 'понедельник',
    1: 'вторник',
    2: 'среда',
    3: 'четверг',
    4: 'пятница',
    5: 'суббота',
    6: 'воскресенье'
}
timemsg = "Текущие дата и время по МСК: "
delta = datetime.timedelta(hours=3)
utc = datetime.timezone.utc
fmt = '%d-%m-%Y %H:%M:%S'


@plugin.on_command('время', 'дата', 'тайм', 'сколько время?', 'сколько время', 'сколько времени?')
async def get_time(msg, args):
    # Знаю, быдлокод. В идеале нужно брать временную зону Москвы и т.д

    time = (datetime.datetime.now(utc) + delta)
    timestr = time.strftime(fmt)

    await msg.answer(timemsg + '\n'
                     + str(timestr) + '\n'
                     + 'Сегодня ' + str(days[time.weekday()]))
