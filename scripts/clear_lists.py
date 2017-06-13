from database import *

'''
С помощью этого скрипта вы можете очистить списки бота.
После выполнения этой программы необходимо перезапустить бота,
чтобы изменения вступили в силу.
'''

if __name__ == '__main__':
    if database:
        delete_lists = [
            "blacklisted",  # чёрный список
            "whitelisted",  # белый список
            "admin",  # список администраторов
        ]

        for list_role in delete_lists:
            Role.delete().where(Role.role == list_role).execute()
