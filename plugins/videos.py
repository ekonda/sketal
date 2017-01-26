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
        await msg.answer('Ничего не найдено')
        return
    count = len(vids)  # Сколько видео мы нашли
    if not count:
        await msg.answer('Ничего не найдено')
    respstr = ''
    for i in range(count):
        respstr += 'video' + str(vids[i]['owner_id']) + '_' + str(vids[i]['id']) + ','
    await msg.answer('Приятного просмотра!', attachment=respstr)
