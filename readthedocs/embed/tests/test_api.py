import pytest
from django.urls import reverse
from django_dynamic_fixture import get
from rest_framework import status

from readthedocs.builds.constants import LATEST
from readthedocs.projects.constants import PUBLIC
from readthedocs.projects.models import Project
from readthedocs.subscriptions.constants import TYPE_EMBED_API
from readthedocs.subscriptions.products import RTDProductFeature


@pytest.mark.django_db
class BaseTestEmbedAPI:
    @pytest.fixture(autouse=True)
    def setup_method(self, settings):
        self.project = get(
            Project,
            language="en",
            main_language_project=None,
            slug="project",
            privacy_level=PUBLIC,
        )
        self.version = self.project.versions.get(slug=LATEST)
        self.version.privacy_level = PUBLIC
        self.version.save()

        settings.PUBLIC_DOMAIN = "readthedocs.io"
        settings.RTD_DEFAULT_FEATURES = dict(
            [RTDProductFeature(TYPE_EMBED_API).to_item()]
        )

    def get(self, client, *args, **kwargs):
        """Wrapper around ``client.get`` to be overridden in the proxied api tests."""
        return client.get(*args, **kwargs)

    def test_is_deprecated(self, client):
        response = self.get(
            client=client,
            path=reverse("embed_api"),
        )
        assert response.status_code == status.HTTP_410_GONE


class TestEmbedAPI(BaseTestEmbedAPI):
    pass


@pytest.mark.proxito
class TestProxiedEmbedAPI(BaseTestEmbedAPI):
    host = "project.readthedocs.io"

    def get(self, client, *args, **kwargs):
        r = client.get(*args, HTTP_HOST=self.host, **kwargs)
        return r
