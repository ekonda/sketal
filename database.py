import datetime
import time

import hues
import peewee
import peewee_async

try:
    from settings import DATABASE_SETTINGS, DATABASE_DRIVER, DATABASE_CHARSET
except:
    DATABASE_SETTINGS, DATABASE_DRIVER, DATABASE_CHARSET = (), None, "utf8mb4"

additional_values = {}
if DATABASE_DRIVER == "mysql":
    driver = peewee_async.MySQLDatabase
    additional_values['charset'] = DATABASE_CHARSET
elif DATABASE_DRIVER == "postgresql":
    driver = peewee_async.PostgresqlDatabase
else:
    driver = None

if len(DATABASE_SETTINGS) == 0:
    database = False
elif len(DATABASE_SETTINGS) == 1:
    name, = DATABASE_SETTINGS
    database = driver(name)
else:
    name, host, port, user, password = DATABASE_SETTINGS
    database = driver(name,
                      host=host,
                      port=port,
                      user=user,
                      password=password,
                      **additional_values)


async def get_or_none(model, *args, **kwargs):
    try:
        return await db.get(model, *args, **kwargs)

    except peewee.DoesNotExist:
        return None

async def set_up_roles(bot):
    from settings import BLACKLIST, WHITELIST, ADMINS

    if WHITELIST:
        bot.WHITELISTED = True

    for u in WHITELIST:
        await db.get_or_create(Role, user_id=u, role="whitelisted")

    for u in BLACKLIST:
        await db.get_or_create(Role, user_id=u, role="blacklisted")

    for u in ADMINS:
        await db.get_or_create(Role, user_id=u, role="admin")

    await check_white_list(bot)


async def check_white_list(bot):
    if await db.count(Role.select().where(Role.role == "whitelisted")) > 0:
        bot.WHITELISTED = True

    else:
        bot.WHITELISTED = False


#############################################################################################
class BaseModel(peewee.Model):
    class Meta:
        database = database


class Role(BaseModel):
    user_id = peewee.BigIntegerField()
    role = peewee.TextField()
    # blacklisted - юзер забанен
    # whitelisted - юзер находится в белом списке
    # admin - юзер является админом


class User(BaseModel):
    uid = peewee.BigIntegerField(primary_key=True, unique=True)
    message_date = peewee.BigIntegerField(default=0)
    in_group = peewee.BooleanField(default=False)

    do_not_disturb = peewee.BooleanField(default=False)
    memory = peewee.TextField(default="")

    chat_data = peewee.TextField(default="")


class Ignore(BaseModel):
    ignored = peewee.ForeignKeyField(User, related_name='ignored_by')
    ignored_by = peewee.ForeignKeyField(User, related_name='ignored')

    class Meta:
        indexes = (
            (('ignored', 'ignored_by'), True),
        )


class ListForMail(BaseModel):
    user_id = peewee.BigIntegerField(unique=True)
    date = peewee.DateTimeField(default=datetime.datetime.now())


class BotStatus(BaseModel):
    last_top = peewee.TextField(default="")
    mail_data = peewee.TextField(default="")

    photos = peewee.IntegerField(default=0)
    timestamp = peewee.IntegerField(default=time.time())


if database:
    db = peewee_async.Manager(database)

    User.create_table(True)
    Ignore.create_table(True)
    ListForMail.create_table(True)
    BotStatus.create_table(True)
    Role.create_table(True)

else:
    hues.error("Не удалось создать базу данных! Проверьте настройки и попробуйте снова!")
