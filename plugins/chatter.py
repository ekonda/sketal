from chatterbot import ChatBot

from plugin_system import Plugin

try:
    from settings import USE_CHATTER
except ImportError:
    USE_CHATTER = False

if not USE_CHATTER:
    plugin = Plugin('Переписка с ботом',
                    usage=['бот [сообщение] - сообщение боту'])

    chatbot = ChatBot(
        'Валера',
        trainer='chatterbot.trainers.ChatterBotCorpusTrainer'
    )

    chatbot.train("chatterbot.corpus.russian")


    @plugin.on_command('бот', 'бот,')
    async def chat(msg, args):
        return await msg.answer(str(chatbot.get_response(msg.text)))
