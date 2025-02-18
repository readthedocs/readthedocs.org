from corsheaders.middleware import (
    ACCESS_CONTROL_ALLOW_CREDENTIALS,
    ACCESS_CONTROL_ALLOW_ORIGIN,
)
from django.test import TestCase, override_settings
from django.test.client import RequestFactory
from django_dynamic_fixture import get

from readthedocs.builds.constants import LATEST
from readthedocs.core.middleware import NullCharactersMiddleware
from readthedocs.projects.constants import PRIVATE, PUBLIC
from readthedocs.projects.models import Domain, Project, ProjectRelationship
from readthedocs.rtd_tests.utils import create_user
from readthedocs.subscriptions.constants import TYPE_EMBED_API
from readthedocs.subscriptions.products import RTDProductFeature


@override_settings(
    PUBLIC_DOMAIN="readthedocs.io",
    RTD_DEFAULT_FEATURES=dict([RTDProductFeature(type=TYPE_EMBED_API).to_item()]),
)
class TestCORSMiddleware(TestCase):
    def setUp(self):
        self.url = "/api/v2/search"
        self.owner = create_user(username="owner", password="test")
        self.project = get(
            Project,
            slug="pip",
            users=[self.owner],
            privacy_level=PUBLIC,
            main_language_project=None,
        )
        self.project.versions.update(privacy_level=PUBLIC)
        self.version = self.project.versions.get(slug=LATEST)
        self.subproject = get(
            Project,
            users=[self.owner],
            privacy_level=PUBLIC,
            main_language_project=None,
        )
        self.subproject.versions.update(privacy_level=PUBLIC)
        self.version_subproject = self.subproject.versions.get(slug=LATEST)
        self.relationship = get(
            ProjectRelationship,
            parent=self.project,
            child=self.subproject,
        )
        self.domain = get(
            Domain,
            domain="my.valid.domain",
            project=self.project,
        )
        self.another_project = get(
            Project,
            privacy_level=PUBLIC,
            slug="another",
        )
        self.another_project.versions.update(privacy_level=PUBLIC)
        self.another_version = self.another_project.versions.get(slug=LATEST)
        self.another_domain = get(
            Domain,
            domain="another.valid.domain",
            project=self.another_project,
        )

    def test_allow_linked_domain_from_public_version(self):
        resp = self.client.get(
            self.url,
            {"project": self.project.slug, "version": self.version.slug},
            headers={"origin": "http://my.valid.domain"},
        )
        self.assertIn(ACCESS_CONTROL_ALLOW_ORIGIN, resp.headers)
        self.assertNotIn(ACCESS_CONTROL_ALLOW_CREDENTIALS, resp.headers)

    def test_linked_domain_from_private_version(self):
        self.version.privacy_level = PRIVATE
        self.version.save()
        resp = self.client.get(
            self.url,
            {"project": self.project.slug, "version": self.version.slug},
            headers={"origin": "http://my.valid.domain"},
        )
        self.assertIn(ACCESS_CONTROL_ALLOW_ORIGIN, resp.headers)
        self.assertNotIn(ACCESS_CONTROL_ALLOW_CREDENTIALS, resp.headers)

    def test_allowed_api_public_version_from_another_domain(self):
        resp = self.client.get(
            self.url,
            {"project": self.project.slug, "version": self.version.slug},
            headers={"origin": "http://docs.another.domain"},
        )
        self.assertIn(ACCESS_CONTROL_ALLOW_ORIGIN, resp.headers)
        self.assertNotIn(ACCESS_CONTROL_ALLOW_CREDENTIALS, resp.headers)

        resp = self.client.get(
            self.url,
            {"project": self.project.slug, "version": self.version.slug},
            headers={"origin": "http://another.valid.domain"},
        )
        self.assertIn(ACCESS_CONTROL_ALLOW_ORIGIN, resp.headers)
        self.assertNotIn(ACCESS_CONTROL_ALLOW_CREDENTIALS, resp.headers)

    def test_api_private_version_from_another_domain(self):
        self.version.privacy_level = PRIVATE
        self.version.save()
        resp = self.client.get(
            self.url,
            {"project": self.project.slug, "version": self.version.slug},
            headers={"origin": "http://docs.another.domain"},
        )
        self.assertIn(ACCESS_CONTROL_ALLOW_ORIGIN, resp.headers)
        self.assertNotIn(ACCESS_CONTROL_ALLOW_CREDENTIALS, resp.headers)

        resp = self.client.get(
            self.url,
            {"project": self.project.slug, "version": self.version.slug},
            headers={"origin": "http://another.valid.domain"},
        )
        self.assertIn(ACCESS_CONTROL_ALLOW_ORIGIN, resp.headers)
        self.assertNotIn(ACCESS_CONTROL_ALLOW_CREDENTIALS, resp.headers)

    def test_valid_subproject(self):
        self.assertTrue(
            Project.objects.filter(
                pk=self.project.pk,
                subprojects__child=self.subproject,
            ).exists(),
        )
        resp = self.client.get(
            self.url,
            {"project": self.project.slug, "version": self.version.slug},
            headers={"origin": "http://my.valid.domain"},
        )
        self.assertIn(ACCESS_CONTROL_ALLOW_ORIGIN, resp.headers)
        self.assertNotIn(ACCESS_CONTROL_ALLOW_CREDENTIALS, resp.headers)

    def test_embed_api_private_version_linked_domain(self):
        self.version.privacy_level = PRIVATE
        self.version.save()
        resp = self.client.get(
            "/api/v2/embed/",
            {"project": self.project.slug, "version": self.version.slug},
            headers={"origin": "http://my.valid.domain"},
        )
        self.assertIn(ACCESS_CONTROL_ALLOW_ORIGIN, resp.headers)
        self.assertNotIn(ACCESS_CONTROL_ALLOW_CREDENTIALS, resp.headers)

    def test_embed_api_external_url(self):
        resp = self.client.get(
            "/api/v2/embed/",
            {"url": "https://pip.readthedocs.io/en/latest/index.hml"},
            headers={"origin": "http://my.valid.domain"},
        )
        self.assertIn("Access-Control-Allow-Origin", resp.headers)

        resp = self.client.get(
            "/api/v2/embed/",
            {"url": "https://docs.example.com/en/latest/index.hml"},
            headers={"origin": "http://my.valid.domain"},
        )
        self.assertIn("Access-Control-Allow-Origin", resp.headers)

    def test_sustainability_endpoint_allways_allowed(self):
        resp = self.client.get(
            "/api/v2/sustainability/",
            {
                "project": self.project.slug,
                "active": True,
                "version": self.version.slug,
            },
            headers={"origin": "http://invalid.domain"},
        )
        self.assertIn(ACCESS_CONTROL_ALLOW_ORIGIN, resp.headers)
        self.assertNotIn(ACCESS_CONTROL_ALLOW_CREDENTIALS, resp.headers)

        resp = self.client.get(
            "/api/v2/sustainability/",
            {
                "project": self.project.slug,
                "active": True,
                "version": self.version.slug,
            },
            headers={"origin": "http://my.valid.domain"},
        )
        self.assertIn(ACCESS_CONTROL_ALLOW_ORIGIN, resp.headers)
        self.assertNotIn(ACCESS_CONTROL_ALLOW_CREDENTIALS, resp.headers)

    def test_apiv2_endpoint_not_allowed(self):
        resp = self.client.get(
            "/api/v2/version/",
            {
                "project": self.project.slug,
                "active": True,
                "version": self.version.slug,
            },
            headers={"origin": "http://invalid.domain"},
        )
        self.assertNotIn(ACCESS_CONTROL_ALLOW_ORIGIN, resp.headers)
        self.assertNotIn(ACCESS_CONTROL_ALLOW_CREDENTIALS, resp.headers)

        # This also doesn't work on registered domains.
        resp = self.client.get(
            "/api/v2/version/",
            {
                "project": self.project.slug,
                "active": True,
                "version": self.version.slug,
            },
            headers={"origin": "http://my.valid.domain"},
        )
        self.assertNotIn(ACCESS_CONTROL_ALLOW_ORIGIN, resp.headers)
        self.assertNotIn(ACCESS_CONTROL_ALLOW_CREDENTIALS, resp.headers)

        # Or from our public domain.
        resp = self.client.get(
            "/api/v2/version/",
            {
                "project": self.project.slug,
                "active": True,
                "version": self.version.slug,
            },
            headers={"origin": "http://docs.readthedocs.io/"},
        )
        self.assertNotIn(ACCESS_CONTROL_ALLOW_ORIGIN, resp.headers)
        self.assertNotIn(ACCESS_CONTROL_ALLOW_CREDENTIALS, resp.headers)

        # POST is not allowed
        resp = self.client.post(
            "/api/v2/version/",
            {
                "project": self.project.slug,
                "active": True,
                "version": self.version.slug,
            },
            headers={"origin": "http://my.valid.domain"},
        )
        self.assertNotIn(ACCESS_CONTROL_ALLOW_ORIGIN, resp.headers)
        self.assertNotIn(ACCESS_CONTROL_ALLOW_CREDENTIALS, resp.headers)


class TestNullCharactersMiddleware(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = NullCharactersMiddleware(None)

    def test_request_with_null_chars(self):
        request = self.factory.get("/?language=en\x00es&project_slug=myproject")
        response = self.middleware(request)
        self.assertContains(
            response,
            "There are NULL (0x00) characters in at least one of the parameters passed to the request.",
            status_code=400,
        )
