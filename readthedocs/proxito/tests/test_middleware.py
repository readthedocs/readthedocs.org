# Copied from test_middleware.py

import pytest
from django.test import TestCase
from django.test.utils import override_settings
from django_dynamic_fixture import get

from readthedocs.builds.models import Version
from readthedocs.projects.constants import PUBLIC
from readthedocs.projects.models import Domain, Project, ProjectRelationship
from readthedocs.proxito.middleware import ProxitoMiddleware
from readthedocs.rtd_tests.base import RequestFactoryTestMixin
from readthedocs.rtd_tests.utils import create_user


@pytest.mark.proxito
@override_settings(PUBLIC_DOMAIN='dev.readthedocs.io')
class MiddlewareTests(RequestFactoryTestMixin, TestCase):

    def setUp(self):
        self.middleware = ProxitoMiddleware()
        self.url = '/'
        self.owner = create_user(username='owner', password='test')
        self.pip = get(
            Project,
            slug='pip',
            users=[self.owner],
            privacy_level='public'
        )

    def run_middleware(self, request):
        return self.middleware.process_request(request)

    def test_proper_cname(self):
        domain = 'docs.random.com'
        get(Domain, project=self.pip, domain=domain)
        request = self.request(self.url, HTTP_HOST=domain)
        res = self.run_middleware(request)
        self.assertIsNone(res)
        self.assertEqual(request.cname, True)
        self.assertEqual(request.host_project_slug, 'pip')

    def test_proper_cname_https_upgrade(self):
        cname = 'docs.random.com'
        get(Domain, project=self.pip, domain=cname, canonical=True, https=True)

        for url in (self.url, '/subdir/'):
            request = self.request(url, HTTP_HOST=cname)
            res = self.run_middleware(request)
            self.assertIsNone(res)
            self.assertTrue(hasattr(request, 'canonicalize'))
            self.assertEqual(request.canonicalize, 'https')

    def test_canonical_cname_redirect(self):
        """Requests to the public domain URL should redirect to the custom domain if the domain is canonical/https."""
        cname = 'docs.random.com'
        domain = get(Domain, project=self.pip, domain=cname, canonical=False, https=False)

        request = self.request(self.url, HTTP_HOST='pip.dev.readthedocs.io')
        res = self.run_middleware(request)
        self.assertIsNone(res)
        self.assertFalse(hasattr(request, 'canonicalize'))

        # Make the domain canonical/https and make sure we redirect
        domain.canonical = True
        domain.https = True
        domain.save()
        for url in (self.url, '/subdir/'):
            request = self.request(url, HTTP_HOST='pip.dev.readthedocs.io')
            res = self.run_middleware(request)
            self.assertIsNone(res)
            self.assertTrue(hasattr(request, 'canonicalize'))
            self.assertEqual(request.canonicalize, 'canonical-cname')

    # We are not canonicalizing custom domains -> public domain for now
    @pytest.mark.xfail(strict=True)
    def test_canonical_cname_redirect_public_domain(self):
        """Requests to a custom domain should redirect to the public domain or canonical domain if not canonical."""
        cname = 'docs.random.com'
        domain = get(Domain, project=self.pip, domain=cname, canonical=False, https=False)

        request = self.request(self.url, HTTP_HOST=cname)
        res = self.run_middleware(request)
        self.assertIsNone(res)
        self.assertTrue(hasattr(request, 'canonicalize'))
        self.assertEqual(request.canonicalize, 'noncanonical-cname')

        # Make the domain canonical and make sure we don't redirect
        domain.canonical = True
        domain.save()
        for url in (self.url, '/subdir/'):
            request = self.request(url, HTTP_HOST=cname)
            res = self.run_middleware(request)
            self.assertIsNone(res)
            self.assertFalse(hasattr(request, 'canonicalize'))

    def test_proper_cname_uppercase(self):
        get(Domain, project=self.pip, domain='docs.random.com')
        request = self.request(self.url, HTTP_HOST='docs.RANDOM.COM')
        self.run_middleware(request)
        self.assertEqual(request.cname, True)
        self.assertEqual(request.host_project_slug, 'pip')

    def test_invalid_cname(self):
        self.assertFalse(Domain.objects.filter(domain='my.host.com').exists())
        request = self.request(self.url, HTTP_HOST='my.host.com')
        r = self.run_middleware(request)
        # We show the 404 error page
        self.assertContains(r, 'my.host.com', status_code=404)

    def test_proper_subdomain(self):
        request = self.request(self.url, HTTP_HOST='pip.dev.readthedocs.io')
        self.run_middleware(request)
        self.assertEqual(request.subdomain, True)
        self.assertEqual(request.host_project_slug, 'pip')

    @override_settings(PUBLIC_DOMAIN='foo.bar.readthedocs.io')
    def test_subdomain_different_length(self):
        request = self.request(
            self.url, HTTP_HOST='pip.foo.bar.readthedocs.io'
        )
        self.run_middleware(request)
        self.assertEqual(request.subdomain, True)
        self.assertEqual(request.host_project_slug, 'pip')

    def test_request_header(self):
        request = self.request(
            self.url, HTTP_HOST='some.random.com', HTTP_X_RTD_SLUG='pip'
        )
        self.run_middleware(request)
        self.assertEqual(request.rtdheader, True)
        self.assertEqual(request.host_project_slug, 'pip')

    def test_request_header_uppercase(self):
        request = self.request(
            self.url, HTTP_HOST='some.random.com', HTTP_X_RTD_SLUG='PIP'
        )
        self.run_middleware(request)

        self.assertEqual(request.rtdheader, True)
        self.assertEqual(request.host_project_slug, 'pip')

    def test_long_bad_subdomain(self):
        domain = 'www.pip.dev.readthedocs.io'
        request = self.request(self.url, HTTP_HOST=domain)
        res = self.run_middleware(request)
        self.assertEqual(res.status_code, 400)


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
