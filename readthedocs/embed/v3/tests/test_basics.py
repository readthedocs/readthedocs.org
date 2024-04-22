import pytest
from django.conf import settings
from django.core.cache import cache
from django.urls import reverse


@pytest.mark.django_db
@pytest.mark.embed_api
class TestEmbedAPIv3Basics:
    @pytest.fixture(autouse=True)
    def setup_method(self, settings):
        settings.PUBLIC_DOMAIN = "readthedocs.io"
        settings.RTD_EMBED_API_EXTERNAL_DOMAINS = [r"^docs\.project\.com$"]

        self.api_url = reverse("embed_api_v3")

        yield
        cache.clear()

    def test_not_url_query_argument(self, client):
        params = {}
        response = client.get(self.api_url, params)
        assert response.status_code == 400
        assert response.json() == {"error": 'Invalid arguments. Please provide "url".'}

    def test_not_allowed_domain(self, client):
        params = {
            "url": "https://docs.notalloweddomain.com#title",
        }
        response = client.get(self.api_url, params)
        assert response.status_code == 400
        assert response.json() == {
            "error": "External domain not allowed. domain=docs.notalloweddomain.com"
        }

    def test_malformed_url(self, client):
        params = {
            "url": "https:///page.html#title",
        }
        response = client.get(self.api_url, params)
        assert response.status_code == 400
        assert response.json() == {
            "error": f'The URL requested is malformed. url={params["url"]}'
        }

    def test_rate_limit_domain(self, client):
        params = {
            "url": "https://docs.project.com#title",
        }
        cache_key = "embed-api-docs.project.com"
        cache.set(cache_key, settings.RTD_EMBED_API_DOMAIN_RATE_LIMIT)

        response = client.get(self.api_url, params)
        assert response.status_code == 429
        assert response.json() == {
            "error": "Too many requests for this domain. domain=docs.project.com"
        }

    def test_infinite_redirect(self, client, requests_mock):
        requests_mock.get(
            "https://docs.project.com",
            status_code=302,
            headers={
                "Location": "https://docs.project.com",
            },
        )
        params = {
            "url": "https://docs.project.com#title",
        }
        response = client.get(self.api_url, params)
        assert response.status_code == 400
        assert response.json() == {
            "error": f'The URL requested generates too many redirects. url={params["url"]}'
        }
