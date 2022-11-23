import pytest

import settings_holder


@pytest.fixture
def settings():
    holder = settings_holder.SettingsWrapper()
    try:
        yield holder
    finally:
        holder.finalize()
