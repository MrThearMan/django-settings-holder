from typing import Any, NamedTuple

from django.test.signals import setting_changed

from settings_holder import SettingsHolder, reload_settings

__all__ = [
    "example_settings",
]


SETTING_NAME: str = "EXAMPLE_SETTINGS"


class ExampleSettings(NamedTuple):
    FOO: str = "bar"


DEFAULTS: dict[str, Any] = ExampleSettings()._asdict()

example_settings = SettingsHolder(
    setting_name=SETTING_NAME,
    defaults=DEFAULTS,
)

reload_my_settings = reload_settings(SETTING_NAME, example_settings)
setting_changed.connect(reload_my_settings)
