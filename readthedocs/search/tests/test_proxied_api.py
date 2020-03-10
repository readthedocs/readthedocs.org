import pytest

from readthedocs.search.tests.test_api import BaseTestDocumentSearch


@pytest.mark.proxito
@pytest.mark.search
class TestProxiedSearchAPI(BaseTestDocumentSearch):

    host = 'pip.readthedocs.io'

    @pytest.fixture(autouse=True)
    def setup_settings(self, settings):
        settings.PUBLIC_DOMAIN = 'readthedocs.io'

    def get_search(self, api_client, search_params):
        return api_client.get(self.url, search_params, HTTP_HOST=self.host)
