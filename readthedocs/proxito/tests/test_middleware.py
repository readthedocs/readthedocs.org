# Copied from test_middleware.py
from unittest import mock

import pytest
from django.core.exceptions import SuspiciousOperation
from django.http import HttpRequest
from django.test import TestCase
from django.test.utils import override_settings
from django_dynamic_fixture import get

from readthedocs.builds.models import Version
from readthedocs.projects.constants import PUBLIC
from readthedocs.projects.models import Domain, Feature, Project, ProjectRelationship
from readthedocs.proxito.constants import RedirectType
from readthedocs.proxito.exceptions import DomainDNSHttp404
from readthedocs.proxito.middleware import ProxitoMiddleware
from readthedocs.rtd_tests.base import RequestFactoryTestMixin
from readthedocs.rtd_tests.storage import BuildMediaFileSystemStorageTest
from readthedocs.rtd_tests.utils import create_user
from readthedocs.subscriptions.constants import TYPE_CNAME


@pytest.mark.proxito
@override_settings(
    PUBLIC_DOMAIN="dev.readthedocs.io",
    RTD_DEFAULT_FEATURES={
        TYPE_CNAME: 1,
    },
)
class MiddlewareTests(RequestFactoryTestMixin, TestCase):

    def setUp(self):
        self.middleware = ProxitoMiddleware()
        self.url = '/'
        self.owner = create_user(username='owner', password='test')
        self.pip = get(
            Project,
            slug='pip',
            users=[self.owner],
            privacy_level=PUBLIC,
        )
        self.pip.versions.update(privacy_level=PUBLIC)

    def run_middleware(self, request):
        return self.middleware.process_request(request)

    def test_proper_cname(self):
        domain = 'docs.random.com'
        get(Domain, project=self.pip, domain=domain)
        request = self.request(
            method="get", secure=True, path=self.url, HTTP_HOST=domain
        )
        res = self.run_middleware(request)
        self.assertIsNone(res)
        self.assertTrue(request.unresolved_domain.is_from_custom_domain)
        self.assertEqual(request.unresolved_domain.project, self.pip)

    def test_proper_cname_https_upgrade(self):
        cname = 'docs.random.com'
        get(Domain, project=self.pip, domain=cname, canonical=True, https=True)

        for url in (self.url, '/subdir/'):
            resp = self.client.get(path=url, secure=False, HTTP_HOST=cname)
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp["location"], f"https://{cname}{url}")
            self.assertEqual(resp["X-RTD-Redirect"], RedirectType.http_to_https.name)

    def test_canonical_cname_redirect(self):
        """Requests to the public domain URL should redirect to the custom domain if the domain is canonical/https."""
        cname = 'docs.random.com'
        domain = get(Domain, project=self.pip, domain=cname, canonical=False, https=False)

        resp = self.client.get(self.url, HTTP_HOST="pip.dev.readthedocs.io")
        # This is the / -> /en/latest/ redirect.
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp["X-RTD-Redirect"], RedirectType.system.name)

        # Make the domain canonical/https and make sure we redirect
        domain.canonical = True
        domain.https = True
        domain.save()
        for url in (self.url, "/subdir/"):
            resp = self.client.get(url, HTTP_HOST="pip.dev.readthedocs.io")
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp["location"], f"https://{cname}{url}")
            self.assertEqual(
                resp["X-RTD-Redirect"], RedirectType.to_canonical_domain.name
            )

    def test_subproject_redirect(self):
        """Requests to a subproject should redirect to the domain of the main project."""
        subproject = get(
            Project,
            name='subproject',
            slug='subproject',
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
            resp = self.client.get(url, HTTP_HOST="subproject.dev.readthedocs.io")
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
        cname = 'docs.random.com'
        get(
            Domain,
            project=subproject,
            domain=cname,
            canonical=True,
            https=True,
        )
        resp = self.client.get(self.url, HTTP_HOST="subproject.dev.readthedocs.io")
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp["location"], f"http://pip.dev.readthedocs.io/projects/subproject/"
        )
        self.assertEqual(
            resp["X-RTD-Redirect"], RedirectType.subproject_to_main_domain.name
        )

    def test_proper_cname_uppercase(self):
        get(Domain, project=self.pip, domain='docs.random.com')
        request = self.request(method='get', path=self.url, HTTP_HOST='docs.RANDOM.COM')
        self.run_middleware(request)
        self.assertTrue(request.unresolved_domain.is_from_custom_domain)
        self.assertEqual(request.unresolved_domain.project, self.pip)

    def test_invalid_cname(self):
        self.assertFalse(Domain.objects.filter(domain='my.host.com').exists())
        request = self.request(method='get', path=self.url, HTTP_HOST='my.host.com')

        with self.assertRaises(DomainDNSHttp404) as cm:
            self.run_middleware(request)

        assert cm.exception.http_status == 404

    def test_proper_subdomain(self):
        request = self.request(method='get', path=self.url, HTTP_HOST='pip.dev.readthedocs.io')
        self.run_middleware(request)
        self.assertTrue(request.unresolved_domain.is_from_public_domain)
        self.assertEqual(request.unresolved_domain.project, self.pip)

    @override_settings(PUBLIC_DOMAIN='foo.bar.readthedocs.io')
    def test_subdomain_different_length(self):
        request = self.request(
            method='get', path=self.url, HTTP_HOST='pip.foo.bar.readthedocs.io'
        )
        self.run_middleware(request)
        self.assertTrue(request.unresolved_domain.is_from_public_domain)
        self.assertEqual(request.unresolved_domain.project, self.pip)

    def test_request_header(self):
        get(
            Feature, feature_id=Feature.RESOLVE_PROJECT_FROM_HEADER, projects=[self.pip]
        )
        request = self.request(
            method='get', path=self.url, HTTP_HOST='some.random.com', HTTP_X_RTD_SLUG='pip'
        )
        self.run_middleware(request)
        self.assertTrue(request.unresolved_domain.is_from_http_header)
        self.assertEqual(request.unresolved_domain.project, self.pip)

    def test_request_header_uppercase(self):
        get(
            Feature, feature_id=Feature.RESOLVE_PROJECT_FROM_HEADER, projects=[self.pip]
        )
        request = self.request(
            method='get', path=self.url, HTTP_HOST='some.random.com', HTTP_X_RTD_SLUG='PIP'
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
        domain = 'www.pip.dev.readthedocs.io'
        request = self.request(method='get', path=self.url, HTTP_HOST=domain)
        with self.assertRaises(DomainDNSHttp404) as cm:
            self.run_middleware(request)

        assert cm.exception.http_status == 400

    def test_front_slash(self):
        domain = 'pip.dev.readthedocs.io'

        # The HttpRequest needs to be created manually,
        # because the RequestFactory strips leading /'s
        request = HttpRequest()
        request.path = '//'
        request.META = {'HTTP_HOST': domain}
        res = self.run_middleware(request)
        self.assertEqual(res.status_code, 302)
        self.assertEqual(
            res['Location'], '/',
        )

        request.path = '///'
        res = self.run_middleware(request)
        self.assertEqual(res.status_code, 302)
        self.assertEqual(
            res['Location'], '/',
        )

        request.path = '////'
        res = self.run_middleware(request)
        self.assertEqual(res.status_code, 302)
        self.assertEqual(
            res['Location'], '/',
        )

        request.path = '////?foo'
        res = self.run_middleware(request)
        self.assertEqual(res.status_code, 302)
        self.assertEqual(
            res['Location'], '/%3Ffoo',  # Encoded because it's in the middleware
        )

    def test_front_slash_url(self):
        domain = 'pip.dev.readthedocs.io'

        # The HttpRequest needs to be created manually,
        # because the RequestFactory strips leading /'s
        request = HttpRequest()
        request.path = '//google.com'
        request.META = {'HTTP_HOST': domain}
        res = self.run_middleware(request)
        self.assertEqual(res.status_code, 302)
        self.assertEqual(
            res['Location'], '/google.com',
        )


class ProxitoV2MiddlewareTests(MiddlewareTests):
    # TODO: remove this class once the new implementation is the default.
    def setUp(self):
        super().setUp()
        get(
            Feature,
            feature_id=Feature.USE_UNRESOLVER_WITH_PROXITO,
            default_true=True,
            future_default_true=True,
        )


@pytest.mark.proxito
@override_settings(PUBLIC_DOMAIN='dev.readthedocs.io')
class MiddlewareURLConfTests(TestCase):

    def setUp(self):
        self.owner = create_user(username='owner', password='test')
        self.domain = 'pip.dev.readthedocs.io'
        self.pip = get(
            Project,
            slug='pip',
            users=[self.owner],
            privacy_level=PUBLIC,
            urlconf='subpath/to/$version/$language/$filename'  # Flipped
        )
        self.testing_version = get(
            Version,
            slug='testing',
            project=self.pip,
            built=True,
            active=True,
        )
        self.pip.versions.update(privacy_level=PUBLIC)

    def test_proxied_api_methods(self):
        # This is mostly a unit test, but useful to make sure the below tests work
        self.assertEqual(self.pip.proxied_api_url, 'subpath/to/_/')
        self.assertEqual(self.pip.proxied_api_host, '/subpath/to/_')

    def test_middleware_urlconf(self):
        resp = self.client.get('/subpath/to/testing/en/foodex.html', HTTP_HOST=self.domain)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp['X-Accel-Redirect'],
            '/proxito/media/html/pip/testing/foodex.html',
        )

    def test_middleware_urlconf_redirects_subpath_root(self):
        resp = self.client.get('/subpath/to/', HTTP_HOST=self.domain)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp['Location'],
            'http://pip.dev.readthedocs.io/subpath/to/latest/en/',
        )

    def test_middleware_urlconf_redirects_root(self):
        resp = self.client.get('/', HTTP_HOST=self.domain)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp['Location'],
            'http://pip.dev.readthedocs.io/subpath/to/latest/en/',
        )

    def test_middleware_urlconf_invalid(self):
        resp = self.client.get('/subpath/to/latest/index.html', HTTP_HOST=self.domain)
        self.assertEqual(resp.status_code, 404)

    def test_middleware_urlconf_subpath_downloads(self):
        # These aren't configurable yet
        resp = self.client.get('/subpath/to/_/downloads/en/latest/pdf/', HTTP_HOST=self.domain)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp['X-Accel-Redirect'],
            '/proxito/media/pdf/pip/latest/pip.pdf',
        )

    def test_middleware_urlconf_subpath_api(self):
        # These aren't configurable yet
        resp = self.client.get(
            '/subpath/to/_/api/v2/footer_html/?project=pip&version=latest&language=en&page=index',
            HTTP_HOST=self.domain
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(
            resp,
            'Inserted RTD Footer',
        )

    @mock.patch(
        "readthedocs.proxito.views.mixins.staticfiles_storage",
        new=BuildMediaFileSystemStorageTest(),
    )
    def test_middleware_urlconf_subpath_static_files(self):
        resp = self.client.get(
            "/subpath/to/_/static/javascript/readthedocs-doc-embed.js",
            HTTP_HOST=self.domain,
        )
        self.assertEqual(resp.status_code, 200)

    def test_urlconf_is_escaped(self):
        self.pip.urlconf = '3.6/$version/$language/$filename'
        self.pip.save()

        self.assertEqual(self.pip.proxied_api_url, '3.6/_/')
        self.assertEqual(self.pip.proxied_api_host, '/3.6/_')

        resp = self.client.get('/316/latest/en/index.html', HTTP_HOST=self.domain)
        self.assertEqual(resp.status_code, 404)
        resp = self.client.get('/3.6/latest/en/index.html', HTTP_HOST=self.domain)
        self.assertEqual(resp.status_code, 200)

        resp = self.client.get('/316/_/downloads/en/latest/pdf/', HTTP_HOST=self.domain)
        self.assertEqual(resp.status_code, 404)
        resp = self.client.get('/3.6/_/downloads/en/latest/pdf/', HTTP_HOST=self.domain)
        self.assertEqual(resp.status_code, 200)

        resp = self.client.get(
            '/316/_/api/v2/footer_html/?project=pip&version=latest&language=en&page=index',
            HTTP_HOST=self.domain
        )
        self.assertEqual(resp.status_code, 404)
        resp = self.client.get(
            '/3.6/_/api/v2/footer_html/?project=pip&version=latest&language=en&page=index',
            HTTP_HOST=self.domain
        )
        self.assertEqual(resp.status_code, 200)



@pytest.mark.proxito
@override_settings(PUBLIC_DOMAIN='dev.readthedocs.io')
class MiddlewareURLConfSubprojectTests(TestCase):

    def setUp(self):
        self.owner = create_user(username='owner', password='test')
        self.domain = 'pip.dev.readthedocs.io'
        self.pip = get(
            Project,
            name='pip',
            slug='pip',
            users=[self.owner],
            privacy_level=PUBLIC,
            urlconf='subpath/$subproject/$version/$language/$filename'  # Flipped
        )
        self.pip.versions.update(privacy_level=PUBLIC)
        self.subproject = get(
            Project,
            name='subproject',
            slug='subproject',
            users=[self.owner],
            privacy_level=PUBLIC,
            main_language_project=None,
        )
        self.testing_version = get(
            Version,
            slug='testing',
            project=self.subproject,
            built=True,
            active=True,
        )
        self.subproject.versions.update(privacy_level=PUBLIC)
        self.relationship = get(
            ProjectRelationship,
            parent=self.pip,
            child=self.subproject,
        )

    def test_middleware_urlconf_subproject(self):
        resp = self.client.get('/subpath/subproject/testing/en/foodex.html', HTTP_HOST=self.domain)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp['X-Accel-Redirect'],
            '/proxito/media/html/subproject/testing/foodex.html',
        )
