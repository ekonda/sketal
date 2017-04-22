from plugin_system import Plugin
usage=['запомни [строка] - запомнить строку',
                      'напомни - напомнить строку']

plugin = Plugin('Блокнот', usage=usage)


@plugin.on_init()
async def on_init(vk):
    if "memoes" not in plugin.data:
        plugin.data["memoes"] = {}


@plugin.on_command('запомни', 'запиши')
async def memo_write(msg, args):
    string = ' '.join(args)
    plugin.data["memoes"][msg.id] = string
    await msg.answer('Вроде запомнил...')



@plugin.on_command('напомни', 'вспомни')
async def memo_read(msg, args):
    string = plugin.data["memoes"].get(msg.id, "Ничего")
    await msg.answer('Вот что я вспомнил:\n' + string)
