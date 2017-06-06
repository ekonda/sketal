import datetime

from plugin_system import Plugin

plugin = Plugin('Время',
                usage=["время - узнать текущее время"])

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


@plugin.on_command('время', 'дата')
async def get_time(msg, args):
    # Знаю, быдлокод. В идеале нужно брать временную зону Москвы и т.д

    time = (datetime.datetime.now(utc) + delta)
    timestr = time.strftime(fmt)

    await msg.answer(f'{timemsg} \n{timestr} \nСегодня {days[time.weekday()]}')
