from plugin_system import Plugin

plugin = Plugin('Поиск видео')


@plugin.on_command('видео', 'видяшки', 'видюхи', 'видос', 'видосик', 'найди видео', 'найди видео про')
async def video_search(vk, msg, args):
    # Если нет аргументов
    if not args:
        return await vk.respond(msg, {'message': 'Что мне искать?'})

    query = ' '.join(args).capitalize()
    params = {
        'q': query,
        'sort': 2,  # Сортировка по релевантности
        'adult': 0,  # Disable 18+ videos (use safe search)
        'count': 4
    }
    # r = api.query(u'video.search', pars)
    resp = await vk.method('video.search', params)
    vids = resp.get('items')
    # Если не нашли ни одного видео
    if not vids:
        await vk.respond(msg, {'message': 'Ничего не найдено'})
        return

    kol = len(vids)  # Сколько видео нашли
    if not kol:
        await vk.respond(msg, {'message': 'Ничего не найдено'})
    respstr = ''
    for i in range(kol):
        respstr += 'video' + str(vids[i]['owner_id']) + '_' + str(vids[i]['id']) + ','
    await vk.respond(msg, {'message': 'Приятного просмотра! ',
                           'attachment': respstr})
