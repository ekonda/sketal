# -*- coding: utf-8 -*-

import random

class Plugin:
    vk = None
	
    plugin_type = 'command args'

    def __init__(self, vk):
        self.vk = vk
        print('Поиск видео')

    def getkeys(self):
        keys = [u'видос', 'видосик', u'видео', u'поиск', u'найди']
        ret = {}
        for key in keys:
            ret[key] = self
        return ret

    def call(self, msg, args=None):
	
    	if len(args) >= 1:
    		body=''
    		for arg in args[1:]:
    			body = body + ' ' + arg

                req = u' '.join(args)
                pars = {
                    'q': req,
                    'sort': 2,
                    'adult': 0,
                }
                #r = api.query(u'video.search', pars)
                r = self.vk.method('video.search', pars)
                vids = r.get('items')
                if vids is None:
		        	self.vk.respond(msg, {'message': u'Ничего не найдено '})
                if vids is not None:
                    kol = min(len(vids), 4)
                    if kol == 0:
		        	    self.vk.respond(msg, {'message': u'Ничего не найдено '})
                    respstr = u''
                    for i in xrange(kol):
                        respstr += u'video' + unicode(vids[i]['owner_id']) + u'_' + unicode(vids[i]['id']) + u','
                    self.vk.respond(msg, {'message': u'Приятного просмотра! ',
                    'attachment': respstr})      		
    	else:
			self.vk.respond(msg, {'message': 'Что мне искать?'})
