## Sketal's plugins
[**AboutPlugin** `[plugins]`](/plugins/about.py)


Answers with information about bot.

---
[**BirthdayPlugin** `[plugins.content]`](/plugins/content/content_birthday.py)


Answers with birthday for users in group (but no more than `max_users_in_group`), for users in conference.

---
[**CalculatorPlugin** `[plugins.content.content_calculation]`](/plugins/content/content_calculation/calculator_plugin.py)


Calculator plugin

---
[**DialogflowPlugin** `[plugins.content.content_dialogflow]`](/plugins/content/content_dialogflow/dialogflow.py)


Plugin for integrating Dialogflow.

---
[**GraffitiPlugin** `[plugins.content]`](/plugins/content/content_graffiti.py)


Plugin turning image into graffiti.

---
[**MemeDoerPlugin** `[plugins.content.content_meme_doer]`](/plugins/content/content_meme_doer/toptextbottomtext.py)


Answers with picture with custom text on.

---
[**QRCodePlugin** `[plugins.content]`](/plugins/content/content_qrcodegen.py)


Answers with encoded and QR code data specified in command

---
[**QuoteDoerPlugin** `[plugins.content.content_quote_doer]`](/plugins/content/content_quote_doer/quote.py)


Answers with image containing stylish quote.

---
[**RandomPostPlugin** `[plugins.content]`](/plugins/content/content_randompost.py)


Answers with random post from group specified in commgroups

---
[**SmileWritePlugin** `[plugins.content.content_smile_write]`](/plugins/content/content_smile_write/smile_write.py)


Plugin printing text with emojies.

---
[**StatisticsPlugin** `[plugins.content]`](/plugins/content/content_statistics.py)


Stores amount of messages for users in chats. Requires: StoragePlugin.

---
[**VideoPlugin** `[plugins.content]`](/plugins/content/content_video.py)


Plugin sending some videos by request.

---
[**AntifloodPlugin** `[plugins.control]`](/plugins/control/control_antiflood.py)


Forbids users to send messages to bot more often than delay `delay`.
If `absolute` is True, bot wont answer on more than 1 message in delay
time.

---
[**ChatControlPlugin** `[plugins.control]`](/plugins/control/control_chat.py)


Allows admins to ban chats.

---
[**CommandAttacherPlugin** `[plugins.control]`](/plugins/control/control_command_attacher.py)


Forwards command with it's answer.

---
[**DispatchPlugin** `[plugins.control]`](/plugins/control/control_dispatch.py)


Allows admins to send out messages to users.

---
[**ForwardedCheckerPlugin** `[plugins.control]`](/plugins/control/control_forwarded_checker.py)


Checks messages' forwarded messages for commands.

---
[**HelpPlugin** `[plugins.control]`](/plugins/control/control_help.py)


Answers with a user a list with plugins's descriptions from `plugins`.

---
[**NoQueuePlugin** `[plugins.control]`](/plugins/control/control_lock_until_done.py)


Forbids user to send messages to bot while his message is being processing by bot.

---
[**StaffControlPlugin** `[plugins.control]`](/plugins/control/control_staff.py)


Allows admins to ban people and control admins for plugins.
Requires StoragePlugin. Admins are global. Moders are local for chats.

---
[**EchoPlugin** `[plugins]`](/plugins/echo.py)


Answers with a message it received.

---
[**AnagramsPlugin** `[plugins.games]`](/plugins/games/games_anagrams.py)


Answers with information about bot. Requires: StoragePlugin.

---
[**CounterPlugin** `[plugins.miscellaneous]`](/plugins/miscellaneous/misc_counter.py)


Useless plugin for counting up. Requires: StoragePlugin.

---
[**NamerPlugin** `[plugins.miscellaneous]`](/plugins/miscellaneous/misc_namer.py)


Answers with information about bot. Requires: StoragePlugin.

---
[**NotifierPlugin** `[plugins.miscellaneous]`](/plugins/miscellaneous/misc_notifier.py)


Creates notification poping up after specified time

---
[**TimePlugin** `[plugins.miscellaneous]`](/plugins/miscellaneous/misc_show_time.py)


Answers with current date and time.

---
[**ChatGreeterPlugin** `[plugins.multiuser]`](/plugins/multiuser/chat_greeter.py)


Answers with message `motd` when user joins a chat.

---
[**ChatKickerPlugin** `[plugins.multiuser]`](/plugins/multiuser/chat_kicker.py)


Allows admins to kick users for short amount of time.
[prefix][command] [time in seconds if kicking]

---
[**MembersPlugin** `[plugins.multiuser]`](/plugins/multiuser/chat_members.py)


Answers with users in conference. Doesn't show users offline if `show_offline` is False.

---
[**PairPlugin** `[plugins.multiuser]`](/plugins/multiuser/chat_random_pair.py)


Answers with 2 users separated by text `text` defaults to `❤ Любит ❤ `.

---
[**WhoIsPlugin** `[plugins.multiuser]`](/plugins/multiuser/chat_random_whois.py)


Answers with a random user from conference with a title specified in command.

---
[**VoterPlugin** `[plugins.multiuser]`](/plugins/multiuser/chat_vote.py)


This plugin allows users to do votes in chats with ability to kick someone with votekick

---
[**Audio2TextPlugin** `[plugins.outsource]`](/plugins/outsource/outsource_audio2text.py)


Plugin turning audio messages to text.

---
[**EmotionsDetectorPlugin** `[plugins.outsource]`](/plugins/outsource/outsource_emotions_detector.py)


Answers with results of detecting emotions on sent image.

---
[**FacePlugin** `[plugins.outsource]`](/plugins/outsource/outsource_faceapp.py)


Plugin using FaceApp for changing photo.

---
[**JokePlugin** `[plugins.outsource]`](/plugins/outsource/outsource_joke.py)


Plugin sending some jokes.

---
[**SayerPlugin** `[plugins.outsource]`](/plugins/outsource/outsource_sayer.py)


Answers with audio message of user's text

---
[**TranslatePlugin** `[plugins.outsource]`](/plugins/outsource/outsource_translater.py)


Answers with translated text from english to russian or from russian to english.
You can change language pair by passing list of 2 names of desired languages (https://tech.yandex.ru/translate/).

---
[**WeatherPlugin** `[plugins.outsource]`](/plugins/outsource/outsource_weather.py)


Answers with a weather in user's city or on specified addres.

---
[**WikiPlugin** `[plugins.outsource]`](/plugins/outsource/outsource_wiki.py)


Asnwers with found data from wikipedia

---
[**YandexNewsPlugin** `[plugins.outsource]`](/plugins/outsource/outsource_yandex_news.py)


Answers with a news from News.Yandex.

---
[**ChatMetaPlugin** `[plugins.technical]`](/plugins/technical/chatmeta.py)


Adds `chat_info` to messages and events's meta["data_chat"] with
chat's data if available (https://vk.com/dev/messages.getChat). You can
refresh data with coroutine stored in `meta['chat_info_refresh']`.

---
[**StoragePlugin** `[plugins.technical]`](/plugins/technical/storage.py)


Allows users and chats to store persistent data with MongoDB or in
memory. Both storages are siuated in `meta` as `data_user` and
`data_chat` and represented as dictionary with possible basic values
(dict, list, tuple, int, float, str, bool). On the beggining theese
fields are populated and after message processing it is saved to
database.
Data is saved only if was acessed. You can use `sdict`'s methods and
field `changed` for accessing data without saving it.

---
[**TinyDBPlugin** `[plugins.technical]`](/plugins/technical/tynydb.py)


Adds self to messages and event's `data` field.
Through this instance you can access TinyDB instance (data["tinydbproxy"].tinydb).
This plugin should be included first!

---
[**UserMetaPlugin** `[plugins.technical]`](/plugins/technical/usermeta.py)


Adds `user_info` to messages and events's meta with user's data
if available (https://vk.com/dev/users.get). You can refresh data
with coroutine stored in `meta['user_info_refresh']`.

---
