import pytest
from django.core.cache import cache
from rest_framework.test import APIClient

pytest_plugins = ("sphinx.testing.fixtures",)


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture(autouse=True)
def clear_cache():
    """
    Clear the cache after each test.

    We don't usually want to share the cache between test cases.
    We have code that will error, as the cache will
    reference to things that don't exist in other test case.
    """
    # Code run before each test
    yield
    # Code run afer each test
    cache.clear()
