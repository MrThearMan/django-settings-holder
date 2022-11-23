from importlib import import_module
from sys import modules
from typing import Any, Callable, Dict, Mapping, Optional, Sequence, Set, Union


__all__ = [
    "SettingsHolder",
]


class SettingsHolder:
    """Object that allows settings to be accessed with attributes.
    Any setting with string import paths will be automatically resolved.
    """

    def __init__(
        self,
        setting_name: str,
        defaults: Optional[Dict[str, Any]] = None,
        import_strings: Optional[Set[Union[str, bytes]]] = None,
        removed_settings: Optional[Set[str]] = None,
    ):
        """Object that allows settings to be accessed with attributes.
        Any setting with string import paths will be automatically resolved.

        :param setting_name: Name of the settings that the user can use to change
                             the defaults in their project settings -module
        :param defaults: Defaults for the settings.
        :param import_strings: List of settings that should be in string dot import notation.
                               If name is in bytes, the imported function is called immediately
                               on setting attribute access, and the result of the function is
                               returned instead of the function.
        :param removed_settings: Settings that have been removed in the past.
        """

        self.setting_name = setting_name
        self.defaults = defaults or {}
        self.import_strings = import_strings or set()
        self.removed_settings = removed_settings or set()
        self._cached_attrs: Set[str] = set()

    def __getattr__(self, attr: str) -> Any:
        from django.conf import settings

        if attr not in self.defaults:
            if attr in self.removed_settings:
                raise AttributeError(f"This setting has been removed: {attr!r}.")
            raise AttributeError(f"Invalid Setting: {attr!r}.")

        try:
            val = getattr(settings, self.setting_name, {})[attr]
        except KeyError:
            val = self.defaults[attr]

        if attr in self.import_strings:
            val = self.perform_import(val, attr)

        # Settings with bytes will call the imported function immediately
        elif bytes(attr, encoding="utf-8") in self.import_strings:
            val = self.perform_import(val, attr)
            if isinstance(val, list):
                val = [v() if callable(v) else v for v in val]
            elif isinstance(val, dict):
                val = {k: v() if callable(v) else v for k, v in val.items()}
            else:
                val = val()

        # Cache the result
        self._cached_attrs.add(attr)
        setattr(self, attr, val)
        return val

    def perform_import(self, val: str, setting: str) -> Any:  # type: ignore
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

        raise ValueError(f"'{setting}' should be a dot import statement, or a sequence of them. Got '{val}'.")

    @staticmethod
    def import_from_string(val: str, setting: str) -> Callable[..., Any]:
        """Attempt to import a class from a string representation."""

        msg = f"Could not import '{val}' for setting '{setting}'"
        try:
            module_path, class_name = val.rsplit(".", 1)
        except ValueError as error:
            raise ImportError(f"{msg}: {val} doesn't look like a module path.") from error

        if module_path not in modules or (
            # Module is not fully initialized.
            getattr(modules[module_path], "__spec__", None) is not None
            and getattr(modules[module_path].__spec__, "_initializing", False) is True
        ):
            try:
                import_module(module_path)
            except ImportError as error:
                raise ImportError(f"{msg}: {error.__class__.__name__}: {error}.") from error

        try:
            return getattr(modules[module_path], class_name)
        except AttributeError as error:
            raise ImportError(
                f"{msg}: Module '{module_path}' does not define a '{class_name}' attribute/class"
            ) from error

    def reload(self) -> None:
        for attr in self._cached_attrs:
            delattr(self, attr)
        self._cached_attrs.clear()
