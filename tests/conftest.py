"""ShikariMCP test configuration."""

import pytest
from shikari.config import ShikariConfig, set_config


@pytest.fixture(autouse=True, scope="session")
def _default_config():
    """Ensure tests always start with a clean default config."""
    set_config(ShikariConfig())
    yield
    set_config(ShikariConfig())
