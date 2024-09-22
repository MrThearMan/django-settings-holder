from __future__ import annotations

import pytest

from .utils import SettingsWrapper

__all__ = [
    "django_settings",
]


@pytest.fixture
def django_settings() -> SettingsWrapper:
    """A Django settings object which restores changes after the testrun."""
    wrapper = SettingsWrapper()
    try:
        yield wrapper
    finally:
        wrapper.finalize()
