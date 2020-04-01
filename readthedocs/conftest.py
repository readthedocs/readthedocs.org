import pytest
from rest_framework.test import APIClient


try:
    # TODO: this file is read/executed even when called from ``readthedocsinc``,
    # so it's overriding the options that we are defining in the ``conftest.py``
    # from the corporate site. We need to find a better way to avoid this.
    import readthedocsinc
    PYTEST_OPTIONS = ()
except ImportError:
    PYTEST_OPTIONS = (
        # Options to set test environment
        ('community', True),
        ('corporate', False),
        ('environment', 'readthedocs'),
    )


def pytest_configure(config):
    for option, value in PYTEST_OPTIONS:
        setattr(config.option, option, value)


@pytest.fixture(autouse=True)
def settings_modification(settings):
    settings.CELERY_ALWAYS_EAGER = True


@pytest.fixture
def api_client():
    return APIClient()
