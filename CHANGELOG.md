#### sketal v7.4 `happy pony`
Version dedicated to performance updates, removing and unifying plugins.
- Added `Bots Long Poll` https://vk.com/dev/bots_longpoll.
- Added `misc_counter.py`.
- Added `order` field to plugins.
- Added `storage.py`
- Added code for generation `PLUGINS.md` (`plugin/__init__.py` -> `save_doc`, should be used around adding class to `__all__`).
- Added default commands to plugins.
- Added default values to plugins.
- Added method `global_after_*_process` for plugins.
- Changed `README.md` и `settings.py`.
- Changed logger's format.
- Rearranged plugins.
- Removed `dueler.py`, `azino.py`, `russianroulette.py`, `hangman` and `anagram`.
- Removed peewee and peewee_async.
- Removed `base_plugin_command.py`.
- Renamed `bot_runner.py` -> `runner.py`.
- Renamed and rearranged `vk` folder. Renamed to package `skevk`.
- Renamed `bot.py` for running to `run.py`.
- Renamed `base_plugin_command.CommandPlugin` to `base_plugin.CommandPlugin`.

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
