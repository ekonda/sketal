import publicsuffixlist
psl = publicsuffixlist.PublicSuffixList()
from plugin_system import Plugin

import pickle
import os

plugin = Plugin('Послать сообщение',
                usage='!напиши [id] [сообщение] - написать сообщение пользователю\n!скрыть [id] - не получать сообщения от пользователя\n!показать [id] - получать сообщения от пользователя\n!небеспокоить - не получать сообщения вообще\n!беспокоить - получать сообщения от пользователей, не в вашем чёрном списке')

black_list = {}
muted = {}

if not os.path.exists("plugins/msg_sender_data"):
    os.makedirs("plugins/msg_sender_data")

try:
    with open('plugins/msg_sender_data/bl.pkl', 'rb') as f:
        black_list = pickle.load(f)
except:
    pass

try:
    with open('plugins/msg_sender_data/m.pkl', 'rb') as f:
        muted = pickle.load(f)
except:
    pass

DISABLED = ('https', 'http', 'com', 'www', 'ftp', '://')
def check_links(string):
    return any(x in string for x in DISABLED) or bool(psl.privatesuffix(string))

@plugin.on_command('написать', 'напиши', 'лс', 'письмо', group=True)
async def write_msg(msg, args):
    if len(args) < 2 and len(msg.attaches) < 1:
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

    if uid in black_list.get(uid, []):
        return await msg.answer('Вы находитесь у этого пользователя в чёрном списке!')

    if muted.get(sender_id, False):
        return await msg.answer('Этот пользователь попросил его не беспокоить!')

    full_message_data = await msg.vk.method('messages.getById', {'message_ids': msg.msg_id, 'preview_length': 1})

    sender_data = await msg.vk.method('users.get', {'user_ids': msg.id, 'name_case': "gen"})
    sender_data = sender_data[0]

    attaches = []

    if full_message_data:
        for message in full_message_data['items']:
            if "attachments" in message:
                for a in message["attachments"]:
                    a_type = a['type']
                    attach = a_type + str(a[a_type]['owner_id']) + "_" + str(a[a_type]['id'])
                    if 'access_key' in a[a_type]:
                        attach += "_" + a[a_type]['access_key']
                    attaches.append(attach)

    val = {
        'peer_id': uid,
        'message': f"Вам сообщение от {sender_data['first_name']} {sender_data['last_name']}!\n\"{data}\"",
	'attachment': ",".join(attaches)
    }

    result = await msg.vk.method('messages.send', val)
    if not result:
        return await msg.answer('Сообщение не удалось отправить!')
    await msg.answer('Сообщение успешно отправлено!')

@plugin.on_command('скрыть', group=True)
async def ignore(msg, args):
    if len(args) < 1:
        return await msg.answer('Введите ID пользователя для игнорирования.')

    sender_id = msg.id
    ignore_id = args.pop()

    if not ignore_id.isdigit():
        uid = await msg.vk.resolve_name(ignore_id)
    else:
        uid = int(ignore_id)

    if not uid:
        return await msg.answer('Проверьте правильность введёного ID пользователя.')

    black_list[sender_id] = black_list.get(sender_id, []) + [uid]

    with open('plugins/msg_sender_data/bl.pkl', 'wb') as f:
        pickle.dump(black_list, f, pickle.HIGHEST_PROTOCOL)

    await msg.answer(f'Вы не будете получать сообщения от {ignore_id}!')

@plugin.on_command('показать', group=True)
async def uninnore(msg, args):
    if len(args) < 1:
        return await msg.answer('Введите ID пользователя, которого вы хотите перестать игнорировать.')

    sender_id = msg.id
    unignore_id = args.pop()

    if not unignore_id.isdigit():
        uid = await msg.vk.resolve_name(unignore_id)
    else:
        uid = int(unignore_id)

    if not uid:
        return await msg.answer('Проверьте правильность введёного ID пользователя.')

    ignoring = black_list.get(sender_id, [])
    if uid in ignoring:
        ignoring.remove(uid)

    with open('plugins/msg_sender_data/bl.pkl', 'wb') as f:
        pickle.dump(black_list, f, pickle.HIGHEST_PROTOCOL)

    await msg.answer(f'Вы будете получать сообщения от {unignore_id}!')

@plugin.on_command('небеспокоить', group=True)
async def silenceon(msg, args):
    muted[msg.id] = True 

    with open('plugins/msg_sender_data/m.pkl', 'wb') as f:
        pickle.dump(muted, f, pickle.HIGHEST_PROTOCOL)

    await msg.answer('Вы не будете получать сообщения!')

@plugin.on_command('беспокоить', group=True)
async def silenceoff(msg, args):
    muted[msg.id] = False 

    with open('plugins/msg_sender_data/m.pkl', 'wb') as f:
        pickle.dump(muted, f, pickle.HIGHEST_PROTOCOL)

    await msg.answer('Вы будете получать все сообщения!')


