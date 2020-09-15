import pytest

from readthedocs.search.tests.test_api import BaseTestDocumentSearch


@pytest.mark.proxito
@pytest.mark.search
class TestProxiedSearchAPI(BaseTestDocumentSearch):

    # This project slug needs to exist in the ``all_projects`` fixture.
    host = 'docs.readthedocs.io'

    def get_search(self, api_client, search_params):
        # TODO: remove once the api is stable
        search_params['new-api'] = 'true'
        return api_client.get(self.url, search_params, HTTP_HOST=self.host)
