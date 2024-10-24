"""
Here is a template for quick setup:

------------------------------------------------------------------------------
from typing import Any, NamedTuple

from django.test.signals import setting_changed

from settings_holder import SettingsHolder, reload_settings

__all__ = ["my_settings"]


SETTING_NAME: str = "..."


class MySettings(NamedTuple):
    ...


DEFAULTS: dict[str, Any] = MySettings()._asdict()

my_settings = SettingsHolder(
    setting_name=SETTING_NAME,
    defaults=DEFAULTS,
)

reload_my_settings = reload_settings(SETTING_NAME, my_settings)
setting_changed.connect(reload_my_settings)
------------------------------------------------------------------------------
"""

from __future__ import annotations

import sys
from importlib import import_module
from typing import Any, Callable, Mapping, Optional, Sequence, Union

__all__ = [
    "SettingsHolder",
]


class SettingsHolder:
    """
    Object that allows settings to be accessed with attributes.
    Any setting with string import paths will be automatically resolved.
    """

    def __init__(
        self,
        setting_name: str,
        defaults: Optional[dict[str, Any]] = None,
        import_strings: Optional[set[Union[str, bytes]]] = None,
        removed_settings: Optional[set[str]] = None,
        validators: Optional[dict[str, Callable[[Any], None]]] = None,
    ) -> None:
        """
        Object that allows settings to be accessed with attributes.
        Any setting with string import paths will be automatically resolved.

        :param setting_name: Name of the settings that the user can use to change
                             the defaults in their project settings -module
        :param defaults: Defaults for the settings.
        :param import_strings: List of settings that should be in string dot import notation.
                               If name is in bytes, the imported function is called immediately
                               on setting attribute access, and the result of the function is
                               returned instead of the function.
        :param removed_settings: Settings that have been removed in the past.
        :param validators: Validators for the settings. The validators are called on first attribute access.
        """
        self.setting_name = setting_name
        self.defaults = defaults or {}
        self.import_strings = import_strings or set()
        self.removed_settings = removed_settings or set()
        self.validators = validators or {}
        self._cached_attrs: set[str] = set()

    def __getattr__(self, attr: str) -> Any:
        """This gets called on first attribute access, since the setting is not yet cached with setattr()."""
        from django.conf import settings

        if attr not in self.defaults:
            if attr in self.removed_settings:
                msg = f"This setting has been removed: {attr!r}."
                raise AttributeError(msg)
            msg = f"Invalid Setting: {attr!r}."
            raise AttributeError(msg)

        try:
            val = getattr(settings, self.setting_name, {})[attr]
        except KeyError:
            val = self.defaults[attr]

        if attr in self.import_strings:
            val = self.perform_import(val, attr)

        # Settings with bytes will call the imported function immediately
        elif bytes(attr, encoding="utf-8") in self.import_strings:
            val = self.perform_import(val, attr)
            if isinstance(val, Sequence):
                val = [v() if callable(v) else v for v in val]
            elif isinstance(val, Mapping):
                val = {k: v() if callable(v) else v for k, v in val.items()}
            else:
                val = val()

        if attr in self.validators:
            self.validators[attr](val)

        # Cache the result
        self._cached_attrs.add(attr)
        setattr(self, attr, val)
        return val

    def perform_import(self, val: str, setting: str) -> Any:
        """If the given setting is a string import notation, then perform the necessary import or imports."""
        if isinstance(val, str):
            return self.import_from_string(val, setting)
        if isinstance(val, Sequence):
            return [self.import_from_string(item, setting) if isinstance(item, str) else item for item in val]
        if isinstance(val, Mapping):
            return {
                key: self.import_from_string(value, setting) if isinstance(value, str) else value
                for key, value in val.items()
            }

        msg = f"'{setting}' should be a dot import statement, or a sequence of them. Got '{val}'."
        raise ValueError(msg)

    @staticmethod
    def import_from_string(val: str, setting: str) -> Callable[..., Any]:
        """Attempt to import a class from a string representation."""
        msg = f"Could not import '{val}' for setting '{setting}'"
        try:
            module_path, class_name = val.rsplit(".", 1)
        except ValueError as error:
            msg = f"{msg}: {val} doesn't look like a module path."
            raise ImportError(msg) from error

        if module_path not in sys.modules or (
            # Module is not fully initialized.
            getattr(sys.modules[module_path], "__spec__", None) is not None
            and getattr(sys.modules[module_path].__spec__, "_initializing", False) is True
        ):
            try:
                import_module(module_path)
            except ImportError as error:
                msg = f"{msg}: {error.__class__.__name__}: {error}."
                raise ImportError(msg) from error

        try:
            return getattr(sys.modules[module_path], class_name)
        except AttributeError as error:
            msg = f"{msg}: Module '{module_path}' does not define a '{class_name}' attribute/class"
            raise ImportError(msg) from error

    def reload(self) -> None:
        for attr in self._cached_attrs:
            delattr(self, attr)
        self._cached_attrs.clear()
