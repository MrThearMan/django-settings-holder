from __future__ import annotations

from dataclasses import dataclass
from functools import wraps
from typing import TYPE_CHECKING, Any, ParamSpec, TypeVar

from django.conf import settings
from django.dispatch import Signal

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Callable

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
    is_immediate: bool
    is_nested: bool


T = TypeVar("T")
P = ParamSpec("P")


def setup_settings_configured_signal() -> None:
    """Setup a signal that fires when settings are configured for the first time."""
    orig_conf = settings.configure
    orig_setup = settings._setup

    configured: bool = False

    def signal_wrapper(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            nonlocal configured

            func(*args, **kwargs)

            if not configured:
                configured = True

                signal_kwargs: dict[str, Any] = {}

                # If _setup() was called, the first argument is the name of the accessed setting.
                if len(args) == 1 and isinstance(args[0], str):
                    signal_kwargs["accessed_setting"] = args[0]

                settings_configured.send(None, **signal_kwargs)

        return wrapper

    object.__setattr__(settings, orig_conf.__name__, signal_wrapper(orig_conf))
    object.__setattr__(settings, orig_setup.__name__, signal_wrapper(orig_setup))


settings_configured = Signal()
"""Sent when settings are configured for the first time."""

setup_settings_configured_signal()
