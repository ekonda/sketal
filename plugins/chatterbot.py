# from plugin_system import Plugin
# try:
#    from chatterbot import ChatBot
# except:
#        pass
# chatbot = ChatBot(
#    'Капитан Очевидность+',
#    trainer='chatterbot.trainers.ChatterBotCorpusTrainer'
# )

# Train based on the english corpus
# chatbot.train("chatterbot.corpus.english")

# Train based on english greetings corpus
# chatbot.train("chatterbot.corpus.english.greetings")

# Train based on the english conversations corpus
# chatbot.train("chatterbot.corpus.english.conversations")


# plugin = Plugin(name="Чат бот (на английском)", description="Чат бот (на английском)")

# @plugin.on_command(all_commands=True)
# def on_cmd(vk, msg, args):
#    result = chatbot.get_response(' '.join(args))
#    vk.respond(msg, {'message':result})
