# Setup

You'll need a place for your settings to live. I recommend a `settings.py` file in your library.
Below is a template for such a file with explanations of each part.

```python
# my-library/settings.py
from typing import Any, Callable
from django.test.signals import setting_changed
from settings_holder import SettingsHolder, reload_settings


# Name of setting that the SettingsHolder will hold
# Note that the name must be in ALL CAPS!
SETTING_NAME: str = "..."

# All the settings that the setting accepts, and their defaults
DEFAULTS: dict[str, Any] = {"foo": "bar"}

# If these settings contain strings, or list or dict containing
# strings, they will be considered "dot import strings" to functions.
# The SettingsHolder will try to import these string to functions
# when the corresponding attribute is accessed. If the name is a
# byte string (b"..."), the imported function will be called
# immediately with no arguments, and the result returned
# instead of the imported function.
IMPORT_STRINGS: set[bytes | str] = set()

# Settings that were once available but no longer are.
# Used for better error messages.
REMOVED_SETTINGS: set[str] = set()

# Map settings to functions used to validate those settings.
# Functions should take a single argument, the value of the
# setting, and raise some error if the value is invalid.
# The function should not try to change the value of the setting,
# and any return value will be ignored.
VALIDATORS: dict[str, Callable[[Any], None]] = {}

# Construct the holder object
holder = SettingsHolder(
    setting_name=SETTING_NAME,
    defaults=DEFAULTS,
    import_strings=IMPORT_STRINGS,
    removed_settings=REMOVED_SETTINGS,
    validators=VALIDATORS,
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
> Using a NamedTuple and converting it to a dict for the `DEFAULTS`
> dict can help document the default settings and their types.
>
> ```python
> class DefaultSettings(NamedTuple):
>     # This is the setting description
>     foo: str = "bar"
>
> DEFAULTS = DefaultSettings()._asdict()
> ```


Now, when projects use your extension, they can simply define the setting with the name
you defined as `SETTING_NAME` (lets say it's `MY_SETTINGS`), and your extension will
use these settings instead of your defined defaults.

```python
# project/settings.py

# User defined settings for your library
MY_SETTINGS = {
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

> For testing, there exists a pytest fixture called `django_settings` that
> works similarly to the `settings` fixture in `pytest-django`. This fixture should
> be automatically available with this library.
