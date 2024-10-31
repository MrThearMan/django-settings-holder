from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from .holder import SettingsHolder


__all__ = [
    "SettingsWrapper",
    "reload_settings",
]


def reload_settings(setting_name: str, setting_holder: SettingsHolder) -> Callable[..., None]:
    """
    Prepare a setting holder to be connected to the 'setting_changed' signal.

    :param setting_name: The holder will be reloaded when a setting with this name
                         is changed in the project's settings file.
    :param setting_holder: Holder that should be reloaded.
    :return: Function to connect to the 'setting_changed' signal.
    """

    def wrapper(*args: Any, **kwargs: Any) -> None:
        setting = kwargs["setting"]

        if setting == setting_name:
            setting_holder.reload()

    return wrapper


class SettingsWrapper:
    """Object to enable changing settings during testing."""

    def __init__(self) -> None:
        self.__to_restore = []

    def __delattr__(self, attr: str) -> None:
        from django.test import override_settings

        override = override_settings()
        override.enable()
        from django.conf import settings

        delattr(settings, attr)

        self.__to_restore.append(override)

    def __setattr__(self, attr: str, value: Any) -> None:
        if attr == "_SettingsWrapper__to_restore":
            self.__dict__[attr] = value
            return

        from django.test import override_settings

        override = override_settings(**{attr: value})
        override.enable()
        self.__to_restore.append(override)

    def __getattr__(self, attr: str) -> Any:
        if attr == "_SettingsWrapper__to_restore":
            return self.__dict__[attr]

        from django.conf import settings

        return getattr(settings, attr)

    def finalize(self) -> None:
        for override in reversed(self.__to_restore):
            override.disable()

        del self.__to_restore[:]


@dataclass
class ImportSettingResults:
    is_import: bool
    is_immidiate: bool
    is_nested: bool
