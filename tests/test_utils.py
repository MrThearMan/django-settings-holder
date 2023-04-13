import re
from unittest.mock import patch

import pytest

from settings_holder import SettingsHolder, SettingsWrapper, reload_settings


@pytest.fixture
def settings_fixture():
    wrapper = SettingsWrapper()
    try:
        yield wrapper
    finally:
        wrapper.finalize()


def function():
    """Function to test dot notation importing."""
    return "foo"


def test_settings_holder__defaults(settings):
    holder = SettingsHolder(setting_name="MOCK_SETTING")

    assert holder.setting_name == "MOCK_SETTING"
    assert holder.defaults == dict()
    assert holder.import_strings == set()
    assert holder.removed_settings == set()


def test_settings_holder__setting_cached(settings):
    settings.MOCK_SETTING = {"foo": "bar"}

    holder = SettingsHolder(setting_name="MOCK_SETTING", defaults={"foo": "baz"})
    assert holder._cached_attrs == set()

    with patch("settings_holder.holder.SettingsHolder.__getattr__", side_effect=holder.__getattr__) as mock:
        x = holder.foo

    assert x == "bar"
    mock.assert_called_once()
    assert holder._cached_attrs == {"foo"}

    with patch("settings_holder.holder.SettingsHolder.__getattr__", side_effect=holder.__getattr__) as mock:
        x = holder.foo

    assert x == "bar"
    # __getattribute__ should find cached attribute
    mock.assert_not_called()

    assert holder._cached_attrs == {"foo"}

    holder.reload()
    assert holder._cached_attrs == set()
    with patch("settings_holder.holder.SettingsHolder.__getattr__", side_effect=holder.__getattr__) as mock:
        x = holder.foo

    assert x == "bar"
    mock.assert_called_once()


def test_settings_holder__setting_not_in_defaults(settings):
    settings.MOCK_SETTING = {"foo": "bar"}
    holder = SettingsHolder(
        setting_name="MOCK_SETTING",
        defaults={"foo": "baz"},
    )

    assert holder.defaults == {"foo": "baz"}
    assert holder.import_strings == set()
    assert holder.removed_settings == set()

    with pytest.raises(AttributeError, match="Invalid Setting: 'error'"):
        holder.error  # noqa


def test_settings_holder__using_removed_setting(settings):
    settings.MOCK_SETTING = {"foo": "bar"}
    holder = SettingsHolder(
        setting_name="MOCK_SETTING",
        defaults={"foo": "baz"},
        removed_settings={"fizz"},
    )

    with pytest.raises(AttributeError, match=re.escape("This setting has been removed: 'fizz'.")):
        holder.fizz  # noqa


def test_settings_holder__using_undefined_setting(settings):
    settings.MOCK_SETTING = {"foo": "bar", "fizz": "buzz"}
    holder = SettingsHolder(
        setting_name="MOCK_SETTING",
        defaults={"foo": "baz"},
    )
    with pytest.raises(AttributeError, match=re.escape("Invalid Setting: 'fizz'.")):
        holder.fizz  # noqa


def test_settings_holder__import_function(settings):
    holder = SettingsHolder(
        setting_name="MOCK_SETTING",
        defaults={"foo": "tests.test_utils.function"},
        import_strings={"foo"},
    )

    assert holder.foo == function


def test_settings_holder__import_function__called_on_access(settings):
    holder = SettingsHolder(
        setting_name="MOCK_SETTING",
        defaults={"foo": "tests.test_utils.function"},
        import_strings={b"foo"},
    )

    assert isinstance(holder.foo, str)
    assert holder.foo == "foo"


def test_settings_holder__import_function__list(settings):
    holder = SettingsHolder(
        setting_name="MOCK_SETTING",
        defaults={"foo": ["tests.test_utils.function"]},
        import_strings={"foo"},
    )

    assert isinstance(holder.foo, list)
    assert holder.foo[0] == function


def test_settings_holder__import_function__list__called_on_access(settings):
    holder = SettingsHolder(
        setting_name="MOCK_SETTING",
        defaults={"foo": ["tests.test_utils.function"]},
        import_strings={b"foo"},
    )

    assert isinstance(holder.foo, list)
    assert isinstance(holder.foo[0], str)
    assert holder.foo[0] == "foo"


def test_settings_holder__import_function__dict(settings):
    holder = SettingsHolder(
        setting_name="MOCK_SETTING",
        defaults={"foo": {"bar": "tests.test_utils.function"}},
        import_strings={"foo"},
    )

    assert isinstance(holder.foo, dict)
    assert holder.foo["bar"] == function


def test_settings_holder__import_function__dict__called_on_access(settings):
    holder = SettingsHolder(
        setting_name="MOCK_SETTING",
        defaults={"foo": {"bar": "tests.test_utils.function"}},
        import_strings={b"foo"},
    )

    assert isinstance(holder.foo, dict)
    assert isinstance(holder.foo["bar"], str)
    assert holder.foo["bar"] == "foo"


def test_settings_holder__import_function__does_not_exist(settings):
    holder = SettingsHolder(
        setting_name="MOCK_SETTING",
        defaults={"foo": "bar"},
        import_strings={"foo"},
    )

    error = f"Could not import 'bar' for setting 'foo': bar doesn't look like a module path."
    with pytest.raises(ImportError, match=error):
        x = holder.foo


def test_settings_holder__import_function__not_valid(settings):
    holder = SettingsHolder(
        setting_name="MOCK_SETTING",
        defaults={"foo": 1},
        import_strings={"foo"},
    )

    error = f"'foo' should be a dot import statement, or a sequence of them. Got '1'."
    with pytest.raises(ValueError, match=error):
        x = holder.foo


def test_settings_holder__import_function__function_does_not_exist(settings):
    holder = SettingsHolder(
        setting_name="MOCK_SETTING",
        defaults={"foo": "tests.test_utils.xxx"},
        import_strings={"foo"},
    )

    error = (
        f"Could not import 'tests.test_utils.xxx' for setting 'foo': "
        f"Module 'tests.test_utils' does not define a 'xxx' attribute/class"
    )
    with pytest.raises(ImportError, match=error):
        x = holder.foo


def test_settings_holder__import_function__module_does_not_exist(settings):
    holder = SettingsHolder(
        setting_name="MOCK_SETTING",
        defaults={"foo": "xxx.test_utils.function"},
        import_strings={"foo"},
    )

    error = f"Could not import 'xxx.test_utils.function' for setting 'foo': ModuleNotFoundError: No module named 'xxx'."
    with pytest.raises(ImportError, match=error):
        x = holder.foo


def test_reload_settings(settings):
    holder = SettingsHolder(
        setting_name="MOCK_SETTING",
        defaults={"foo": "bar"},
    )
    reloader = reload_settings(setting_name="MOCK_SETTING", setting_holder=holder)

    assert holder.foo == "bar"
    settings.MOCK_SETTING = {"foo": "fizzbuzz"}

    # Reload has not happened yet
    assert holder.foo == "bar"

    reloader(value={"foo": "fizzbuzz"}, setting="MOCK_SETTING")

    assert holder.foo == "fizzbuzz"


def test_reload_settings__different_setting(settings):
    holder = SettingsHolder(
        setting_name="MOCK_SETTING",
        defaults={"foo": "bar"},
    )
    reloader = reload_settings(setting_name="MOCK_SETTING", setting_holder=holder)

    assert holder.foo == "bar"

    reloader(value={"foo": "fizzbuzz"}, setting="FOO")

    assert holder.foo == "bar"


def test_settings_wrapper__fixture(settings_fixture):
    assert settings_fixture.TEST_SETTING == "foo"
    settings_fixture.TEST_SETTING = "bar"
    assert settings_fixture.TEST_SETTING == "bar"


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
