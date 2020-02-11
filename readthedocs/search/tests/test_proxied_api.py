import pytest

from readthedocs.search.tests.test_api import TestDocumentSearch


@pytest.mark.urls('readthedocs.proxito.urls')
@pytest.mark.search
class TestProxiedSearchAPI(TestDocumentSearch):

    host = 'pip.readthedocs.io'

    def get_search(self, api_client, search_params):
        return api_client.get(self.url, search_params, HTTP_HOST=self.host)
