# -*- coding: utf-8 -*-
import pytest

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
        setattr(config.option, 'markexpr', 'not search')

    for option, value in PYTEST_OPTIONS:
        setattr(config.option, option, value)


@pytest.fixture(autouse=True)
def settings_modification(settings):
    settings.CELERY_ALWAYS_EAGER = True
