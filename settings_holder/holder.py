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
from collections.abc import Callable, Mapping, Sequence
from importlib import import_module
from typing import Any, Optional, Union

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from .utils import ImportSettingResults, settings_configured

__all__ = [
    "SettingsHolder",
]


class SettingsHolder:
    """Object that allows settings to be accessed with attributes and automatically updated from user settings."""

    def __init__(
        self,
        setting_name: str,
        defaults: Optional[dict[str, Any]] = None,
        import_strings: Optional[set[Union[str, bytes]]] = None,
        removed_settings: Optional[dict[str, str | None]] = None,
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
        self._setting_name = setting_name
        self._defaults = defaults or {}
        self._imports = import_strings or set()
        self._removed_settings = removed_settings or {}
        self._validators = validators or {}
        self._cached_attrs: set[str] = set()

        dispatch_uid = f"configure_{setting_name.lower()}"
        settings_configured.connect(self.check_user_settings, dispatch_uid=dispatch_uid)
        self._settings_checked = False

        if settings.configured:
            self.check_user_settings()

    def __getattr__(self, attr: str) -> Any:
        if not settings.configured:  # pragma: no cover
            msg = "Settings are not configured."
            raise ImproperlyConfigured(msg)

        if not self._settings_checked:
            self.check_user_settings(accessed_setting=attr)
        else:
            self.check_setting(name=attr)

        user_settings: dict[str, Any] = getattr(settings, self._setting_name, {})

        try:
            value = user_settings[attr]
        except KeyError:
            value = self._defaults[attr]

        value = self.make_imports(attr, value)

        if attr in self._validators:
            self._validators[attr](value)

        # Cache the result by setting the attribute to the holder.
        # With this, accessing the attribute will not trigger this '__getattr__'.
        setattr(self, attr, value)
        return value

    def __setattr__(self, attr: str, val: Any) -> None:
        # If the attribute is not private, and it is a valid setting, note it as cached.
        # This allows 'reload()' to remove the cached attribute from the holder.
        if attr[0] != "_" and attr in self._defaults:
            self._cached_attrs.add(attr)
        super().__setattr__(attr, val)

    def check_user_settings(self, **kwargs: Any) -> None:  # 'kwargs' for signal compatibility
        user_settings: set[str] = set(getattr(settings, self._setting_name, {}))

        accessed_setting = kwargs.get("accessed_setting")
        if accessed_setting is not None:
            user_settings.add(accessed_setting)

        errors: list[str] = []

        for user_setting in user_settings:
            try:
                self.check_setting(user_setting)

            except ImproperlyConfigured as error:  # noqa: PERF203
                errors.append(str(error))

        if errors:
            raise ImproperlyConfigured("\n".join(errors))

        self._settings_checked = True

    def check_setting(self, name: str) -> None:
        if name in self._defaults:
            return

        if name not in self._removed_settings:
            msg = f"Setting '{self._setting_name}.{name}' does not exist."
            raise ImproperlyConfigured(msg)

        new_setting = self._removed_settings[name]

        msg = f"Setting '{self._setting_name}.{name}' has been removed."
        if new_setting is not None:
            msg += f" Use '{self._setting_name}.{new_setting}' instead."

        raise ImproperlyConfigured(msg)

    def make_imports(self, name: str, value: Any) -> Any:
        """Make the necessary imports for the given setting, recursing inside mutable sequences and mappings."""
        results = self.is_import_setting(name)
        if not results.is_import:
            return value

        if not results.is_nested:
            if not isinstance(value, str):
                msg = f"{name!r} should be a string. Got {value!r}."
                raise ValueError(msg)

            value = self.import_from_string(value, name)
            if results.is_immediate:
                return value()
            return value

        if isinstance(value, Sequence):
            return type(value)(self.make_imports(f"{name}.0", val) for val in value)

        if isinstance(value, Mapping):
            return type(value)((key, self.make_imports(f"{name}.{key}", val)) for key, val in value.items())

        msg = f"{name!r} should be a mutable sequence or mapping. Got {value!r}."
        raise ValueError(msg)

    def is_import_setting(self, attr: str) -> ImportSettingResults:
        for value in self._imports:
            is_immediate = isinstance(value, bytes)
            if is_immediate:
                value = value.decode("utf8")  # noqa: PLW2901

            name = self.substitute_wildcards(attr, value)

            if name.startswith(attr):
                is_nested = len(name) > len(attr)
                return ImportSettingResults(is_import=True, is_immediate=is_immediate, is_nested=is_nested)

        return ImportSettingResults(is_import=False, is_immediate=False, is_nested=False)

    def substitute_wildcards(self, attr: str, value: str) -> str:
        """Substitute wildcards in 'value' with the matching parts in 'attr' when both are split by periods."""
        attr_parts = attr.split(".")
        return ".".join(
            attr_parts[idx] if part == "*" and len(attr_parts) > idx else part
            for idx, part in enumerate(value.split("."))
        )

    @staticmethod
    def import_from_string(val: str, setting: str) -> Callable[..., Any]:
        """
        Attempt to import a class from a string representation.

        Adapted from `django.utils.module_loading.import_string`.
        """
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
        self._settings_checked = False
