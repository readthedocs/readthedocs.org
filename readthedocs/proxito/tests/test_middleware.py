# Copied from test_middleware.py

import pytest
from django.core.exceptions import SuspiciousOperation
from django.http import HttpRequest, HttpResponse
from django.test import TestCase
from django.test.utils import override_settings
from django_dynamic_fixture import get

from readthedocs.projects.constants import PUBLIC
from readthedocs.projects.models import Domain, Feature, Project, ProjectRelationship
from readthedocs.proxito.constants import RedirectType
from readthedocs.proxito.exceptions import DomainDNSHttp404
from readthedocs.proxito.middleware import ProxitoMiddleware
from readthedocs.rtd_tests.base import RequestFactoryTestMixin
from readthedocs.rtd_tests.utils import create_user
from readthedocs.subscriptions.constants import TYPE_CNAME
from readthedocs.subscriptions.products import RTDProductFeature


@pytest.mark.proxito
@override_settings(
    PUBLIC_DOMAIN="dev.readthedocs.io",
    RTD_DEFAULT_FEATURES=dict([RTDProductFeature(type=TYPE_CNAME, value=2).to_item()]),
)
class MiddlewareTests(RequestFactoryTestMixin, TestCase):
    def setUp(self):
        self.middleware = ProxitoMiddleware(lambda request: HttpResponse())
        self.url = "/"
        self.owner = create_user(username="owner", password="test")
        self.pip = get(
            Project,
            slug="pip",
            users=[self.owner],
            privacy_level=PUBLIC,
        )
        self.pip.versions.update(privacy_level=PUBLIC)

    def run_middleware(self, request):
        return self.middleware.process_request(request)

    def test_proper_cname(self):
        domain = "docs.random.com"
        get(Domain, project=self.pip, domain=domain)
        request = self.request(
            method="get", secure=True, path=self.url, HTTP_HOST=domain
        )
        res = self.run_middleware(request)
        self.assertIsNone(res)
        self.assertTrue(request.unresolved_domain.is_from_custom_domain)
        self.assertEqual(request.unresolved_domain.project, self.pip)

    def test_proper_cname_https_upgrade(self):
        cname = "docs.random.com"
        get(Domain, project=self.pip, domain=cname, canonical=True, https=True)

        for url in (self.url, "/subdir/"):
            resp = self.client.get(path=url, secure=False, headers={"host": cname})
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp["location"], f"https://{cname}{url}")
            self.assertEqual(resp["X-RTD-Redirect"], RedirectType.http_to_https.name)

    def test_canonical_cname_redirect(self):
        """Requests to the public domain URL should redirect to the custom domain if the domain is canonical/https."""
        cname = "docs.random.com"
        domain = get(
            Domain, project=self.pip, domain=cname, canonical=False, https=False
        )

        resp = self.client.get(self.url, headers={"host": "pip.dev.readthedocs.io"})
        # This is the / -> /en/latest/ redirect.
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp["X-RTD-Redirect"], RedirectType.system.name)

        # Make the domain canonical/https and make sure we redirect
        domain.canonical = True
        domain.https = True
        domain.save()
        for url in (self.url, "/subdir/"):
            resp = self.client.get(url, headers={"host": "pip.dev.readthedocs.io"})
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp["location"], f"https://{cname}{url}")
            self.assertEqual(
                resp["X-RTD-Redirect"], RedirectType.to_canonical_domain.name
            )

    def test_subproject_redirect(self):
        """Requests to a subproject should redirect to the domain of the main project."""
        subproject = get(
            Project,
            name="subproject",
            slug="subproject",
            users=[self.owner],
            privacy_level=PUBLIC,
        )
        subproject.versions.update(privacy_level=PUBLIC)
        get(
            ProjectRelationship,
            parent=self.pip,
            child=subproject,
        )

        for url in (self.url, "/subdir/", "/en/latest/"):
            resp = self.client.get(
                url, headers={"host": "subproject.dev.readthedocs.io"}
            )
            self.assertEqual(resp.status_code, 302)
            self.assertTrue(
                resp["location"].startswith(
                    "http://pip.dev.readthedocs.io/projects/subproject/"
                )
            )
            self.assertEqual(
                resp["X-RTD-Redirect"], RedirectType.subproject_to_main_domain.name
            )

        # Using a custom domain in a subproject isn't supported (or shouldn't be!).
        cname = "docs.random.com"
        get(
            Domain,
            project=subproject,
            domain=cname,
            canonical=True,
            https=True,
        )
        resp = self.client.get(
            self.url, headers={"host": "subproject.dev.readthedocs.io"}
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp["location"], f"http://pip.dev.readthedocs.io/projects/subproject/"
        )
        self.assertEqual(
            resp["X-RTD-Redirect"], RedirectType.subproject_to_main_domain.name
        )

    def test_proper_cname_uppercase(self):
        get(Domain, project=self.pip, domain="docs.random.com")
        request = self.request(method="get", path=self.url, HTTP_HOST="docs.RANDOM.COM")
        self.run_middleware(request)
        self.assertTrue(request.unresolved_domain.is_from_custom_domain)
        self.assertEqual(request.unresolved_domain.project, self.pip)

    def test_invalid_cname(self):
        self.assertFalse(Domain.objects.filter(domain="my.host.com").exists())
        request = self.request(method="get", path=self.url, HTTP_HOST="my.host.com")

        with self.assertRaises(DomainDNSHttp404) as cm:
            self.run_middleware(request)

        assert cm.exception.http_status == 404

    def test_proper_subdomain(self):
        request = self.request(
            method="get", path=self.url, HTTP_HOST="pip.dev.readthedocs.io"
        )
        self.run_middleware(request)
        self.assertTrue(request.unresolved_domain.is_from_public_domain)
        self.assertEqual(request.unresolved_domain.project, self.pip)

    @override_settings(PUBLIC_DOMAIN="foo.bar.readthedocs.io")
    def test_subdomain_different_length(self):
        request = self.request(
            method="get", path=self.url, HTTP_HOST="pip.foo.bar.readthedocs.io"
        )
        self.run_middleware(request)
        self.assertTrue(request.unresolved_domain.is_from_public_domain)
        self.assertEqual(request.unresolved_domain.project, self.pip)

    def test_request_header(self):
        get(
            Feature, feature_id=Feature.RESOLVE_PROJECT_FROM_HEADER, projects=[self.pip]
        )
        request = self.request(
            method="get",
            path=self.url,
            HTTP_HOST="some.random.com",
            HTTP_X_RTD_SLUG="pip",
        )
        self.run_middleware(request)
        self.assertTrue(request.unresolved_domain.is_from_http_header)
        self.assertEqual(request.unresolved_domain.project, self.pip)

    def test_request_header_uppercase(self):
        get(
            Feature, feature_id=Feature.RESOLVE_PROJECT_FROM_HEADER, projects=[self.pip]
        )
        request = self.request(
            method="get",
            path=self.url,
            HTTP_HOST="some.random.com",
            HTTP_X_RTD_SLUG="PIP",
        )
        self.run_middleware(request)

        self.assertTrue(request.unresolved_domain.is_from_http_header)
        self.assertEqual(request.unresolved_domain.project, self.pip)

    def test_request_header_not_allowed(self):
        request = self.request(
            method="get",
            path=self.url,
            HTTP_HOST="docs.example.com",
            HTTP_X_RTD_SLUG="pip",
        )
        with pytest.raises(SuspiciousOperation):
            self.run_middleware(request)

    def test_long_bad_subdomain(self):
        domain = "www.pip.dev.readthedocs.io"
        request = self.request(method="get", path=self.url, HTTP_HOST=domain)
        with self.assertRaises(DomainDNSHttp404) as cm:
            self.run_middleware(request)

        assert cm.exception.http_status == 400

    def test_front_slash(self):
        domain = "pip.dev.readthedocs.io"

        # The HttpRequest needs to be created manually,
        # because the RequestFactory strips leading /'s
        request = HttpRequest()
        request.path = "//"
        request.META = {"HTTP_HOST": domain}
        res = self.run_middleware(request)
        self.assertEqual(res.status_code, 302)
        self.assertEqual(
            res["Location"],
            "/",
        )

        request.path = "///"
        res = self.run_middleware(request)
        self.assertEqual(res.status_code, 302)
        self.assertEqual(
            res["Location"],
            "/",
        )

        request.path = "////"
        res = self.run_middleware(request)
        self.assertEqual(res.status_code, 302)
        self.assertEqual(
            res["Location"],
            "/",
        )

        request.path = "////?foo"
        res = self.run_middleware(request)
        self.assertEqual(res.status_code, 302)
        self.assertEqual(
            res["Location"],
            "/%3Ffoo",  # Encoded because it's in the middleware
        )

    def test_front_slash_url(self):
        domain = "pip.dev.readthedocs.io"

        # The HttpRequest needs to be created manually,
        # because the RequestFactory strips leading /'s
        request = HttpRequest()
        request.path = "//google.com"
        request.META = {"HTTP_HOST": domain}
        res = self.run_middleware(request)
        self.assertEqual(res.status_code, 302)
        self.assertEqual(
            res["Location"],
            "/google.com",
        )
