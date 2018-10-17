# -*- coding: utf-8 -*-
import pytest

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

        ('url_scheme', 'http'),
    )


def pytest_addoption(parser):
    parser.addoption(
        '--including-search',
        action='store_true',
        dest='searchtests',
        default=False, help='enable search tests',
    )


def pytest_configure(config):
    if not config.option.searchtests:
        # Include ``not search``` to parameters so search tests do not perform
        markexpr = getattr(config.option, 'markexpr')
        if markexpr:
            markexpr += ' and not search'
        else:
            markexpr = 'not search'
        setattr(config.option, 'markexpr', markexpr.strip())

    for option, value in PYTEST_OPTIONS:
        setattr(config.option, option, value)


@pytest.fixture(autouse=True)
def settings_modification(settings):
    settings.CELERY_ALWAYS_EAGER = True
