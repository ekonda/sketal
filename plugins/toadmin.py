from plugin_system import Plugin
from settings import ADMINS

plugin = Plugin('Сообщение админу',
                usage=['админу [текст] - отослать администрации сообщение'])


@plugin.on_command('админу')
async def toadmin(msg, args):
    data = ' '.join(args)

    sender_data = await msg.vk.method('users.get', {'user_ids': msg.user_id, 'name_case': "gen"})
    sender_data = sender_data[0]

    for uid in ADMINS:
        val = {
            'peer_id': uid,
            'message': f"Сообщение от {sender_data['first_name']} {sender_data['last_name']}, (vk.com/id{msg.id}):"
                       f"\n\"{data}\"",
        }

        if "attach1" in msg.brief_attaches:
            val['attachment'] = ",".join(str(x) for x in await msg.full_attaches)

        result = await msg.vk.method('messages.send', val)

    if not result:
        return await msg.answer('Сообщение не удалось отправить!')

    await msg.answer('Сообщение успешно отправлено!')
