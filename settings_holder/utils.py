from __future__ import annotations

from typing import TYPE_CHECKING, Callable


if TYPE_CHECKING:
    from .holder import SettingsHolder


__all__ = ["reload_settings"]


def reload_settings(setting_name: str, setting_holder: SettingsHolder) -> Callable[..., None]:
    """Prepare a setting holder to be connected to the 'setting_changed' signal.

    :param setting_name: The holder will be reloaded when a setting with this name
                         is changed in the project's settings file.
    :param setting_holder: Holder that should be reloaded.
    :return: Function to connect to the 'setting_changed' signal.
    """

    def wrapper(*args, **kwargs) -> None:  # pylint: disable=W0613
        setting, value = kwargs["setting"], kwargs["value"]

        if setting == setting_name:
            setting_holder.reload(new_user_settings=value)

    return wrapper
