from plugin_system import Plugin

plugin = Plugin('Поиск видео')

possible_commands = ('видео', 'видяшки', 'видос', 'видосик', 'найди видео',
                     'найди видео про', 'видео про', 'видос про')


@plugin.on_command(*possible_commands)
async def video_search(msg, args):
    # Если нет аргументов
    if not args:
        return await msg.answer('Какое видео вас интересует?')

    query = ' '.join(args)
    params = {
        'q': query,
        'sort': 2,  # Сортировка по релевантности
        'adult': 0,  # Включить "взрослый" контент
        'count': 5  # Кол-во результатов
    }
    resp = await msg.vk.method('video.search', params)
    vids = resp.get('items')
    # Если не нашли ни одного видео
    if not vids:
        return await msg.answer('Ничего не найдено')
    resp = ','.join('video{}_{}'.format(vid['owner_id'], vid['id']) for vid in vids)
    await msg.answer('Приятного просмотра!', attachment=resp)
