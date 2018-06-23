#### sketal v8.0.0 `happy pony`
Version dedicated to performance updates, removing and unifying plugins.
- Added `Bots Long Poll` https://vk.com/dev/bots_longpoll.
- Added `control_chat.py`.
- Added `control_staff.py`.
- Added `misc_counter.py`.
- Added `content_namer.py`.
- Added `content_statistics.py`
- Added `games_anagrams.py`
- Added `control_friends.py`
- Added `order` field to plugins.
- Added highly optimized plugin `storage.py`.
- Added code for generation `PLUGINS.md` (`plugin/__init__.py` -> `save_doc`, should be used around adding class to `__all__`).
- Added default commands to plugins.
- Added default values to plugins.
- Added method `global_after_*_process` for plugins.
- Added `_nl_to_text` and `_nl_to_br` for method execution.
- Added more tests(!) and enchanced them.
- Added error handling
- Added `reserved_by` to `Message`
- Changed `README.md`.
- Changed `ISSUE_TEMPLATE.py`.
- Changed `settings.py`.
- Changed logger's format.
- Changed `Makefile`.
- Changed life control methods of bot.
- Changed many base plugins (!important!).
- Rearranged plugins.
- Removed `dueler.py`.
- Removed `azino.py`.
- Removed `russianroulette.py`.
- Removed `hangman` and `anagram`.
- Removed `anagram`.
- Removed peewee and peewee_async.
- Removed `base_plugin_command.py`.
- Removed `occupied_by` and `reserved_by`
- Removed mass methods (it wasn't useful).
- Renamed `bot_runner.py` -> `runner.py`.
- Renamed `admin` to `control_staff_control.py` and reworked it.
- Renamed and rearranged `vk` folder. Renamed to package `utils`.
- Renamed `bot.py` for running to `run.py`.
- Renamed `base_plugin_command.CommandPlugin` to `base_plugin.CommandPlugin`.
- Fixed `control_friends.py`
- Many fixes.
- Moved `utils.py` to `utils/routine.py`

#### sketal v7.3.4 `funny dog`
https://github.com/vk-brain/sketal/commit/e320bc87694a88ea0019cbd11f0a254cb2a55293

##### update v7.3.4
- Minor bug fixes
- Added some plugins: `audio2text`...

##### update v7.3.3
- Now bot only working from it's first user or group

##### update v7.3.2
- Extended README.md
- Fixed `DuelerPlugin`
- Fixed BasePlugin's `get_path`.
- Added `groups.isMember` to ALLOWED_METHODS.
- Moved tests.

##### update v7.3.1
- Still `Code style` fixes and optimizations
- Got rid of `exec` in plugins' `__init__.py`
- Moved `calculation` plugin in `content`
- Rearranged files:
  - `methods.py` -> `vk/methods.py`
  - `vk_auth.py` -> `vk/auth.py`
  - `vk_data.py` -> `vk/data.py`
  - `vk_api.py` -> `vk/api.py`
  - `vk_special_methods.py` -> `vk/helpers.py`
  - `vk_plus.py` -> `vk/plus.py`
  - `vk_utils.py` -> `vk/utils.py`

##### update v7.3
- Many `Code style` fixes
- Fixed couple of bugs in dueler
- Fixed user parsing
- Revomed `ChatterPlugin`

##### patch #1
- Added `DialogflowPlugin`
- Moved `BirthdayPlugin`
- From now on, https://semver.org/ will be used as guide to versioning. Quote:
```
For version: MAJOR.MINOR.PATCH
MAJOR version when you make incompatible API changes,
MINOR version when you add functionality in a backwards-compatible manner, and
PATCH version when you make backwards-compatible bug fixes.
```

##### patch #0
- Added `CHANGELOG.md`
- Changed msg.`data` and evnt.`data` to msg.`meta` and evnt.`meta`
- Upgrated `parse_user_id`
- Added `ChatMetaPlugin`
- Added `VoterPlugin`
- Fixed `CommandPlugin`
