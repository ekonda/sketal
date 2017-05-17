import peewee
import peewee_async

try:
    from settings import DATABASE_SETTINGS, DATABASE_DRIVER
except:
    DATABASE_SETTINGS, DATABASE_DRIVER = (), None

if DATABASE_DRIVER == "mysql":
    driver = peewee_async.MySQLDatabase
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
                      password=password)


async def get_or_none(model, *args, **kwargs):
    try:
        return await db.get(model, *args, **kwargs)

    except peewee.DoesNotExist:
        return None


class BaseModel(peewee.Model):
    class Meta:
        database = database


class User(BaseModel):
    uid = peewee.BigIntegerField(primary_key=True, unique=True)
    message_date = peewee.BigIntegerField(default=0)
    in_group = peewee.BooleanField(default=False)

    do_not_disturb = peewee.BooleanField(default=False)
    memory = peewee.TextField(default="")


class Ignore(BaseModel):
    ignored = peewee.ForeignKeyField(User, related_name='ignored_by')
    ignored_by = peewee.ForeignKeyField(User, related_name='ignored')

    class Meta:
        indexes = (
            (('ignored', 'ignored_by'), True),
        )

if database:
    db = peewee_async.Manager(database)

    User.create_table(True)
    Ignore.create_table(True)

else:
    from fake_database import *
