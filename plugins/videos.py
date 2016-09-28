from plugin_system import Plugin

plugin = Plugin('Поиск видео')


@plugin.on_command('видео', 'видяшки', 'видюхи', 'видос', 'видосик', 'найди видео')
def video_search(vk, msg, args):
    if len(args) > 0:
        body = ''
        for arg in args[0:]:
            body = body + ' ' + arg

        req = ' '.join(args)
        params = {
            'q': req,
            'sort': 2,
            'adult': 1,
        }
        # r = api.query(u'video.search', pars)
        resp = vk.method('video.search', params)
        vids = resp.get('items')
        if vids is None:
            vk.respond(msg, {'message': 'Ничего не найдено'})
            return
        if vids is not None:
            kol = min(len(vids), 4)
            if kol == 0:
                vk.respond(msg, {'message': 'Ничего не найдено'})
            respstr = ''
            for i in range(kol):
                respstr += 'video' + str(vids[i]['owner_id']) + '_' + str(vids[i]['id']) + ','
            vk.respond(msg, {'message': 'Приятного просмотра! ',
                                  'attachment': respstr})
    else:
        vk.respond(msg, {'message': 'Что мне искать?'})
