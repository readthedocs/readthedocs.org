import pytest
from rest_framework.test import APIClient

pytest_plugins = 'sphinx.testing.fixtures'

@pytest.fixture
def api_client():
    return APIClient()
