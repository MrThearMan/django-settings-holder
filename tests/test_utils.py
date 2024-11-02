# ruff: noqa: PGH004
from unittest.mock import patch

import pytest

from settings_holder import SettingsHolder, SettingsWrapper, reload_settings
from tests.helpers import exact


def function():
    """Function to test dot notation importing."""
    return "foo"


def test_settings_holder__defaults():
    holder = SettingsHolder(setting_name="MOCK_SETTING")

    assert holder._setting_name == "MOCK_SETTING"
    assert holder._defaults == {}
    assert holder._imports == set()
    assert holder._removed_settings == set()


def test_settings_holder__setting_cached(django_settings):
    django_settings.MOCK_SETTING = {"FOO": "bar"}

    holder = SettingsHolder(setting_name="MOCK_SETTING", defaults={"FOO": "baz"})
    assert holder._cached_attrs == set()

    with patch("settings_holder.holder.SettingsHolder.__getattr__", side_effect=holder.__getattr__) as mock:
        x = holder.FOO

    assert x == "bar"
    mock.assert_called_once()
    assert holder._cached_attrs == {"FOO"}

    with patch("settings_holder.holder.SettingsHolder.__getattr__", side_effect=holder.__getattr__) as mock:
        x = holder.FOO

    assert x == "bar"
    # __getattribute__ should find cached attribute
    mock.assert_not_called()

    assert holder._cached_attrs == {"FOO"}

    holder.reload()
    assert holder._cached_attrs == set()
    with patch("settings_holder.holder.SettingsHolder.__getattr__", side_effect=holder.__getattr__) as mock:
        x = holder.FOO

    assert x == "bar"
    mock.assert_called_once()


def test_settings_holder__setting_not_in_defaults(django_settings):
    django_settings.MOCK_SETTING = {"FOO": "bar"}
    holder = SettingsHolder(
        setting_name="MOCK_SETTING",
        defaults={"FOO": "baz"},
    )

    assert holder._defaults == {"FOO": "baz"}
    assert holder._imports == set()
    assert holder._removed_settings == set()

    msg = "Invalid Setting: 'ERROR'."
    with pytest.raises(AttributeError, match=exact(msg)):
        x = holder.ERROR


def test_settings_holder__using_removed_setting(django_settings):
    django_settings.MOCK_SETTING = {"FOO": "bar"}
    holder = SettingsHolder(
        setting_name="MOCK_SETTING",
        defaults={"FOO": "baz"},
        removed_settings={"FIZZ"},
    )

    msg = "This setting has been removed: 'FIZZ'."
    with pytest.raises(AttributeError, match=exact(msg)):
        x = holder.FIZZ


def test_settings_holder__using_undefined_setting(django_settings):
    django_settings.MOCK_SETTING = {"FOO": "bar", "FIZZ": "buzz"}
    holder = SettingsHolder(
        setting_name="MOCK_SETTING",
        defaults={"FOO": "baz"},
    )

    msg = "Invalid Setting: 'FIZZ'."
    with pytest.raises(AttributeError, match=exact(msg)):
        x = holder.FIZZ


def test_settings_holder__setting_validator(django_settings):
    def validator(value: str) -> None:
        if value != "bar":
            msg = "Value must be 'bar'."
            raise ValueError(msg)

    django_settings.MOCK_SETTING = {"FOO": "bar", "FIZZ": "buzz"}
    holder = SettingsHolder(
        setting_name="MOCK_SETTING",
        defaults={"FOO": "1", "FIZZ": "bar"},
        validators={"FOO": validator, "FIZZ": validator},
    )
    x = holder.FOO

    msg = "Value must be 'bar'."
    with pytest.raises(ValueError, match=exact(msg)):
        x = holder.FIZZ


def test_settings_holder__import_function():
    holder = SettingsHolder(
        setting_name="MOCK_SETTING",
        defaults={"FOO": "tests.test_utils.function"},
        import_strings={"FOO"},
    )

    assert function == holder.FOO


def test_settings_holder__import_function__called_on_access():
    holder = SettingsHolder(
        setting_name="MOCK_SETTING",
        defaults={"FOO": "tests.test_utils.function"},
        import_strings={b"FOO"},
    )

    assert isinstance(holder.FOO, str)
    assert holder.FOO == "foo"


def test_settings_holder__import_function__list():
    holder = SettingsHolder(
        setting_name="MOCK_SETTING",
        defaults={"FOO": ["tests.test_utils.function"]},
        import_strings={"FOO.0"},
    )

    assert isinstance(holder.FOO, list)
    assert holder.FOO[0] == function


def test_settings_holder__import_function__tuple():
    holder = SettingsHolder(
        setting_name="MOCK_SETTING",
        defaults={"FOO": ("tests.test_utils.function",)},
        import_strings={"FOO.0"},
    )

    assert isinstance(holder.FOO, tuple)
    assert holder.FOO[0] == function


def test_settings_holder__import_function__list__called_on_access():
    holder = SettingsHolder(
        setting_name="MOCK_SETTING",
        defaults={"FOO": ["tests.test_utils.function"]},
        import_strings={b"FOO.0"},
    )

    assert isinstance(holder.FOO, list)
    assert isinstance(holder.FOO[0], str)
    assert holder.FOO[0] == "foo"


def test_settings_holder__import_function__dict():
    holder = SettingsHolder(
        setting_name="MOCK_SETTING",
        defaults={"FOO": {"BAR": "tests.test_utils.function"}},
        import_strings={"FOO.BAR"},
    )

    assert isinstance(holder.FOO, dict)
    assert holder.FOO["BAR"] == function


def test_settings_holder__import_function__dict__called_on_access():
    holder = SettingsHolder(
        setting_name="MOCK_SETTING",
        defaults={"FOO": {"BAR": "tests.test_utils.function"}},
        import_strings={b"FOO.BAR"},
    )

    assert isinstance(holder.FOO, dict)
    assert isinstance(holder.FOO["BAR"], str)
    assert holder.FOO["BAR"] == "foo"


def test_settings_holder__import_function__dict__all_keys():
    holder = SettingsHolder(
        setting_name="MOCK_SETTING",
        defaults={"FOO": {"BAR": "tests.test_utils.function", "BAZ": "tests.test_utils.function"}},
        import_strings={"FOO.*"},
    )

    assert function == holder.FOO["BAR"]
    assert function == holder.FOO["BAZ"]


def test_settings_holder__import_function__dict__all_keys__not_string():
    holder = SettingsHolder(
        setting_name="MOCK_SETTING",
        defaults={"FOO": {"BAR": {"foo": "tests.test_utils.function"}}},
        import_strings={"FOO.*"},
    )

    error = "'FOO.BAR' should be a string. Got {'foo': 'tests.test_utils.function'}."
    with pytest.raises(ValueError, match=exact(error)):
        x = holder.FOO["BAR"]


def test_settings_holder__import_function__dict__all_keys__deeper():
    holder = SettingsHolder(
        setting_name="MOCK_SETTING",
        defaults={"FOO": {"BAR": {"FOO": "tests.test_utils.function"}}},
        import_strings={"FOO.*.FOO"},
    )

    assert function == holder.FOO["BAR"]["FOO"]


def test_settings_holder__import_function__dict__all_keys__bytes():
    holder = SettingsHolder(
        setting_name="MOCK_SETTING",
        defaults={"FOO": {"BAR": "tests.test_utils.function"}},
        import_strings={b"FOO.*"},
    )

    assert holder.FOO["BAR"] == "foo"


def test_settings_holder__import_function__does_not_exist():
    holder = SettingsHolder(
        setting_name="MOCK_SETTING",
        defaults={"FOO": "bar"},
        import_strings={"FOO"},
    )

    error = "Could not import 'bar' for setting 'FOO': bar doesn't look like a module path."
    with pytest.raises(ImportError, match=exact(error)):
        x = holder.FOO


def test_settings_holder__import_function__not_valid():
    holder = SettingsHolder(
        setting_name="MOCK_SETTING",
        defaults={"FOO": 1},
        import_strings={"FOO"},
    )

    error = "'FOO' should be a string. Got 1."
    with pytest.raises(ValueError, match=exact(error)):
        x = holder.FOO


def test_settings_holder__import_function__not_valid__nested():
    holder = SettingsHolder(
        setting_name="MOCK_SETTING",
        defaults={"FOO": {"BAR": 1}},
        import_strings={"FOO.BAR"},
    )

    error = "'FOO.BAR' should be a string. Got 1."
    with pytest.raises(ValueError, match=exact(error)):
        x = holder.FOO


def test_settings_holder__import_function__not_in_import_strings():
    holder = SettingsHolder(
        setting_name="MOCK_SETTING",
        defaults={"FOO": 1},
        import_strings={"FOO.BAR"},
    )

    error = "'FOO' should be a mutable sequence or mapping. Got 1."
    with pytest.raises(ValueError, match=exact(error)):
        x = holder.FOO


def test_settings_holder__import_function__function_does_not_exist():
    holder = SettingsHolder(
        setting_name="MOCK_SETTING",
        defaults={"FOO": "tests.test_utils.xxx"},
        import_strings={"FOO"},
    )

    error = (
        "Could not import 'tests.test_utils.xxx' for setting 'FOO': "
        "Module 'tests.test_utils' does not define a 'xxx' attribute/class"
    )
    with pytest.raises(ImportError, match=exact(error)):
        x = holder.FOO


def test_settings_holder__import_function__module_does_not_exist():
    holder = SettingsHolder(
        setting_name="MOCK_SETTING",
        defaults={"FOO": "xxx.test_utils.function"},
        import_strings={"FOO"},
    )

    error = "Could not import 'xxx.test_utils.function' for setting 'FOO': ModuleNotFoundError: No module named 'xxx'."
    with pytest.raises(ImportError, match=exact(error)):
        x = holder.FOO


def test_reload_settings(django_settings):
    holder = SettingsHolder(
        setting_name="MOCK_SETTING",
        defaults={"FOO": "bar"},
    )
    reloader = reload_settings(setting_name="MOCK_SETTING", setting_holder=holder)

    assert holder.FOO == "bar"
    django_settings.MOCK_SETTING = {"FOO": "fizzbuzz"}

    # Reload has not happened yet
    assert holder.FOO == "bar"

    reloader(value={"FOO": "fizzbuzz"}, setting="MOCK_SETTING")

    assert holder.FOO == "fizzbuzz"


def test_reload_settings__different_setting():
    holder = SettingsHolder(
        setting_name="MOCK_SETTING",
        defaults={"FOO": "bar"},
    )
    reloader = reload_settings(setting_name="MOCK_SETTING", setting_holder=holder)

    assert holder.FOO == "bar"

    reloader(value={"foo": "fizzbuzz"}, setting="FOO")

    assert holder.FOO == "bar"


def test_settings_wrapper__fixture(django_settings):
    assert django_settings.TEST_SETTING == "foo"
    django_settings.TEST_SETTING = "bar"
    assert django_settings.TEST_SETTING == "bar"


def test_settings_wrapper__nested():
    wrapper1 = SettingsWrapper()

    try:
        assert wrapper1.TEST_SETTING == "foo"
        wrapper1.TEST_SETTING = "bar"
        assert wrapper1.TEST_SETTING == "bar"

        wrapper2 = SettingsWrapper()

        try:
            assert wrapper2.TEST_SETTING == "bar"
            wrapper2.TEST_SETTING = "baz"
            assert wrapper2.TEST_SETTING == "baz"

        finally:
            wrapper2.finalize()

        assert wrapper1.TEST_SETTING == "bar"

    finally:
        wrapper1.finalize()

    assert wrapper1.TEST_SETTING == "foo"


def test_settings_wrapper__delete():
    wrapper = SettingsWrapper()

    try:
        assert wrapper.TEST_SETTING == "foo"
        del wrapper.TEST_SETTING
        assert not hasattr(wrapper, "TEST_SETTING")
    finally:
        wrapper.finalize()

    assert wrapper.TEST_SETTING == "foo"


def test_settings_wrapper__access_restore():
    wrapper = SettingsWrapper()

    try:
        assert wrapper.__getattr__("_SettingsWrapper__to_restore") == []
    finally:
        wrapper.finalize()
