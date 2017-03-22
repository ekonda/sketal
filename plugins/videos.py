from plugin_system import Plugin

plugin = Plugin('Поиск видео',
                usage='видео [строка для поиска] - найти видео по запросу')


@plugin.on_command('видео', 'видяшки', 'видос', 'видосик', group=False)
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
    resp = ','.join(f"video{vid['owner_id']}_{vid['id']}" for vid in vids)
    await msg.answer('Приятного просмотра!', attachment=resp)
