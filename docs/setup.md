# Setup

Define a settings file with `USER_SETTINGS`, `DEFAULTS`, `IMPORT_STRINGS`, and `REMOVED_SETTINGS`.
Then define the SettingsHolder from these. Then, connect the holder to the `setting_changed`-signal.

```python
# my-library/settings.py
from typing import Optional, Dict, Any, Set, Union
from django.conf import settings
from django.test.signals import setting_changed
from settings_holder import SettingsHolder, reload_settings


# Name of setting that the SettingsHolder will hold
# Note that the name must be in ALL CAPS!
SETTING_NAME: str = "..."

# User defined settings from the project settings file
USER_SETTINGS: Optional[Dict[str, Any]] = getattr(settings, SETTING_NAME, None)

# All the settings that the setting accepts, and their defaults
DEFAULTS: Dict[str, Any] = {"foo": "bar"}

# If these settings contain strings, or list or dict containing
# strings, they will be considered "dot import strings" to functions.
# The SettingsHolder will try to import these string to functions
# when the corresponding attribute is accessed. If the name is a
# byte string (b"..."), the imported function will be called
# immidiately with no arguments, and the result returned
# instead of the imported function.
IMPORT_STRINGS: Set[Union[bytes, str]] = set()

# Settings that were once avilable but no longer are.
# Used for better error messages.
REMOVED_SETTINGS: Set[str] = set()

# Construct the holder object
holder = SettingsHolder(
    user_settings=USER_SETTINGS,
    defaults=DEFAULTS,
    import_strings=IMPORT_STRINGS,
    removed_settings=REMOVED_SETTINGS,
)

# Connect the holder object to the 'setting_changed' signal
# so that the settings inside the holder are updated in DEBUG mode.
# NOTE: Function needs to be saved to a variable first
# so that the signal is connected correctly!
reload_my_settings = reload_settings(SETTING_NAME, holder)
setting_changed.connect(reload_my_settings)
```

> Hint:
>
> Using a NamedTuple and converting it to a dict for the DEFAULTS
> dict can help document the default settings and their types.
>
> ```python
> class DefaultSettings(NamedTuple):
>     # This is the setting description
>     foo: str = "bar"
>
> DEFAULTS = DefaultSettings()._asdict()
> ```


Now when projects use your extension, they can simply define the setting with the name
you defined as `SETTING_NAME`, and your extension will use these settings instead of
your defined defaults.

```python
# project/settings.py

# User defined settings for your library
SETTING_NAME = {
    "foo": "baz",
}

```

```python
# my-library/utils.py
from .settings import holder

# The user setting is reflected in the holder.
# It would be the default "bar" if not set by the user.
assert holder.foo == "baz"
```
