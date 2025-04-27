from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

from .utils import SettingsWrapper

if TYPE_CHECKING:
    from collections.abc import Generator

__all__ = [
    "django_settings",
]


@pytest.fixture
def django_settings() -> Generator[SettingsWrapper, Any, None]:
    """A Django settings object which restores changes after the testrun."""
    wrapper = SettingsWrapper()
    try:
        yield wrapper
    finally:
        wrapper.finalize()
