import hues
from playhouse.migrate import *

from database import *

'''
В будущем база данных бота будет изменяться, придётся менять её структуру.
Чтобы свести потери данных к минимуму, в этом файле будут хранится функции,
которые будут стараться преобразовывать базы так, чтобы новые версии с ними
работали.
'''
# http://docs.peewee-orm.com/en/latest/peewee/playhouse.html#SchemaMigrator


def migrate0(migrator):
    """Миграция с версии <5.0 до 5.0"""

    migrate(
        migrator.add_column(BotStatus._meta.db_table, 'mail_data', TextField(default='')),
        migrator.drop_column(BotStatus._meta.db_table, 'name'),
    )

if __name__ == '__main__':
    if database:
        if DATABASE_DRIVER == "mysql":
            migrator = SqliteMigrator(database)

        elif DATABASE_DRIVER == "postgresql":
            migrator = PostgresqlMigrator(database)
        else:
            hues.error("Can't migrate database!")

        with database.transaction():
            'Тут список функций, которее будут производить миграции!'
            'Будте аккуратны с этим!'

            migrate0(migrator)
