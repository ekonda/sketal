from plugin_system import Plugin

plugin = Plugin('Поиск видео')

possible_commands = ('видео', 'видяшки', 'видос', 'видосик', 'найди видео',
                     'найди видео про', 'видео про', 'видос про')

@plugin.on_command(*possible_commands)
async def video_search(msg, args):
    # Если нет аргументов
    if not args:
        return await msg.answer('Что мне искать?')

    query = ' '.join(args).capitalize()
    params = {
        'q': query,
        'sort': 2,  # Сортировка по релевантности
        'adult': 0,  # Включить "взрослый" контент
        'count': 4
    }
    resp = await msg.vk.method('video.search', params)
    vids = resp.get('items')
    # Если не нашли ни одного видео
    if not vids:
        return await msg.answer('Ничего не найдено')
    count = len(vids)  # Сколько видео мы нашли
    if not count:
        return await msg.answer('Ничего не найдено')
    resp = ''
    for vid in vids:
        resp += 'video{oid}_{id},'.format(oid=vid['owner_id'],id=vid['id'])
    await msg.answer('Приятного просмотра!', attachment=resp)
