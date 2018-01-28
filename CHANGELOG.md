#### sketal v7.3.1 `funny dog`
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
