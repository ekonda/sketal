# Словарь, ключ - раздел API методов, значение - список разрешённых методов
ALLOWED_METHODS = {
    'groups': ('getById',
               'getCallbackConfig',
               'getCallbackServer',
               'getCallbackSettings',
               'getMembers',
               'isMember',
               'getOnlineStatus',
               'setCallbackServer',
               'setCallbackServerSettings',
               'setCallbackSettings'),

    'docs': ('getMessagesUploadServer',
             'getWallUploadServer'),

    'photos': ('getMessagesUploadServer',
               'saveMessagesPhoto')
}

# Словарь, ключ - раздел API методов, значение - список запрещённых методов
DISALLOWED_MESSAGES = ('addChatUser',
                       'allowMessagesFromGroup',
                       'createChat',
                       'denyMessagesFromGroup',
                       'deleteChatPhoto',
                       'editChat',
                       'getChat',
                       'getChatUsers',
                       'getLastActivity',
                       'markAsImportant',
                       'removeChatUser',
                       'searchDialogs',
                       'setActivity',
                       'setChatPhoto')


def is_available_from_group(key):
    if key == 'execute':
        return True

    try:
        topic, method = key.split('.')
    except ValueError:
        return False

    if topic == 'messages':
        return method not in DISALLOWED_MESSAGES

    if method in ALLOWED_METHODS.get(topic, ()):
        return True

    return False


# Методы, которые можно выполнять без авторизации API
ALLOWED_PUBLIC = {
    'apps': ('get', 'getCatalog'),

    'auth': ('checkPhone', 'confirm', 'restore', 'signup'),

    'board': ('getComments', 'getTopics'),

    'database': ('getChairs', 'getCities', 'getCitiesById',
                 'getCountries', 'getCountriesById', 'getFaculties',
                 'getRegions', 'getSchoolClasses', 'getSchools',
                 'getStreetsById', 'getUniversities'),

    'friends': ('get',),

    'groups': ('getById', 'getMembers', 'isMember'),

    'likes': ('getList',),

    'newsfeed': ('search',),

    'pages': ('clearCache',),

    'photos': ('get', 'getAlbums', 'getById', 'search'),

    'users': ('get', 'getFollowers', 'getSubscriptions'),

    'utils': ('checkLink', 'getServerTime', 'resolveScreenName'),

    'video': ('getCatalog', 'getCatalogSection'),

    'wall': ('get', 'getById', 'getComments', 'getReposts', 'search'),

    'widgets': ('getComments', 'getPages')
}


def is_available_from_public(key):
    try:
        topic, method = key.split('.')
    except ValueError:
        return False

    if method in ALLOWED_PUBLIC.get(topic, ()):
        return True

    return False
