import publicsuffixlist
psl = publicsuffixlist.PublicSuffixList()
from plugin_system import Plugin

import pickle
import os

plugin = Plugin("Отправка анонимного сообщения",
                usage="!анонимно [id] [сообщение] - написать анонимное сообщение пользователю(посылать можно только текст и/или фото)\n!неполучатьанонимки - не получать анонимные сообщения\n!получатьанонимки - получать анонимные сообщения")

muted = {}

if not os.path.exists("plugins/msg_anon_data"):
    os.makedirs("plugins/msg_anon_data")

try:
    with open('plugins/msg_anon_data/m.pkl', 'rb') as f:
        muted = pickle.load(f)
except:
    pass

DISABLED = ('https', 'http', 'com', 'www', 'ftp', '://')
def check_links(string):
    return any(x in string for x in DISABLED) or bool(psl.privatesuffix(string))

@plugin.on_command('анонимно')
async def anonymously(msg, args):
    text_required = True
    for attach in msg.attaches:
        if attach.type == "photo":
            text_required = False

    if len(args) < 2 and text_required:
        return await msg.answer('Введите ID пользователя и сообщение для него.')

    sender_id = msg.id
    possible_id = args.pop(0)

    if not possible_id.isdigit():
        uid = await msg.vk.resolve_name(possible_id)
    else:
        uid = int(possible_id)

    if not uid:
        return await msg.answer('Проверьте правильность введёного ID пользователя.')

    if sender_id == uid:
        return await msg.answer('Зачем мне отправлять сообщение самому себе?!')

    data = ' '.join(args)

    if check_links(data):
        return await msg.answer('В сообщении были обнаружены ссылки!')

    if muted.get(sender_id, False):
        return await msg.answer('Этот пользователь попросил его не беспокоить!')

    full_message_data = await msg.vk.method('messages.getById', {'message_ids': msg.msg_id, 'preview_length': 1})

    attaches = []

    if full_message_data:
        for message in full_message_data['items']:
            if "attachments" in message:
                for a in message["attachments"]:
                    a_type = a['type']

                    if a_type != "photo":
                        continue

                    link = ""

                    for k in a[a_type]:
                        if "photo_" in k:
                           link = a[a_type][k]

                    if link:
                        attaches += [link]

    if data:
        message = f"Вам анонимное сообщение!\n\"{data}\"\nПриложения:\n" + "\n".join(attaches)
    else:
        message = "Вам анонимное сообщение!\n" + "\n".join(attaches)

    val = {
        'peer_id': uid,
        'message': message
    }

    result = await msg.vk.method('messages.send', val)
    if not result:
        return await msg.answer('Сообщение не удалось отправить!')
    await msg.answer('Сообщение успешно отправлено!')

@plugin.on_command('неполучатьанонимки', group=True)
async def silenceon(msg, args):
    muted[msg.id] = True 

    with open('plugins/msg_anon_data/m.pkl', 'wb') as f:
        pickle.dump(muted, f, pickle.HIGHEST_PROTOCOL)

    await msg.answer('Вы не будете получать сообщения!')

@plugin.on_command('получатьанонимки', group=True)
async def silenceoff(msg, args):
    muted[msg.id] = False 

    with open('plugins/msg_anon_data/m.pkl', 'wb') as f:
        pickle.dump(muted, f, pickle.HIGHEST_PROTOCOL)

    await msg.answer('Вы будете получать все сообщения!')

