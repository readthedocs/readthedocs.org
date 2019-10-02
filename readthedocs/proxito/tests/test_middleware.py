# Copied from test_middleware.py

from django.test import TestCase
from django.test.client import RequestFactory
from django.test.utils import override_settings
from django_dynamic_fixture import get

from readthedocs.projects.models import Domain, Project
from readthedocs.proxito.middleware import ProxitoMiddleware
from readthedocs.rtd_tests.utils import create_user


@override_settings(USE_SUBDOMAIN=True)
@override_settings(PUBLIC_DOMAIN='dev.readthedocs.io')
class MiddlewareTests(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
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
        request = self.factory.get(self.url, HTTP_HOST=domain)
        res = self.run_middleware(request)
        self.assertIsNone(res)
        self.assertEqual(request.cname, True)
        self.assertEqual(request.slug, 'pip')

    def test_proper_cname_uppercase(self):
        get(Domain, project=self.pip, domain='docs.random.com')
        request = self.factory.get(self.url, HTTP_HOST='docs.RANDOM.COM')
        self.run_middleware(request)
        self.assertEqual(request.cname, True)
        self.assertEqual(request.slug, 'pip')

    def test_invalid_cname(self):
        self.assertFalse(Domain.objects.filter(domain='my.host.com').exists())
        request = self.factory.get(self.url, HTTP_HOST='my.host.com')
        r = self.run_middleware(request)
        self.assertEqual(r.status_code, 404)
        # We show the 404 error page
        self.assertTrue(b'my.host.com' in r.content)

    def test_proper_subdomain(self):
        request = self.factory.get(self.url, HTTP_HOST='pip.dev.readthedocs.io')
        self.run_middleware(request)
        self.assertEqual(request.subdomain, True)
        self.assertEqual(request.slug, 'pip')

    @override_settings(PUBLIC_DOMAIN='foo.bar.readthedocs.io')
    def test_subdomain_different_length(self):
        request = self.factory.get(
            self.url, HTTP_HOST='pip.foo.bar.readthedocs.io'
        )
        self.run_middleware(request)
        self.assertEqual(request.subdomain, True)
        self.assertEqual(request.slug, 'pip')

    def test_request_header(self):
        request = self.factory.get(
            self.url, HTTP_HOST='some.random.com', HTTP_X_RTD_SLUG='pip'
        )
        self.run_middleware(request)
        self.assertEqual(request.rtdheader, True)
        self.assertEqual(request.slug, 'pip')

    def test_request_header_uppercase(self):
        request = self.factory.get(
            self.url, HTTP_HOST='some.random.com', HTTP_X_RTD_SLUG='PIP'
        )
        self.run_middleware(request)

        self.assertEqual(request.rtdheader, True)
        self.assertEqual(request.slug, 'pip')

    def test_long_bad_subdomain(self):
        domain = 'www.pip.dev.readthedocs.io'
        request = self.factory.get(self.url, HTTP_HOST=domain)
        res = self.run_middleware(request)
        self.assertEqual(res.status_code, 400)
