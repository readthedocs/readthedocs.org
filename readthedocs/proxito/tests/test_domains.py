from django.conf import settings
from django.http import Http404
from django.test import TestCase
from django.test.client import RequestFactory
from django.test.utils import override_settings
from mock import patch

from proxito.views import serve


@override_settings(USE_SUBDOMAIN=True)
class MiddlewareTests(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.view = serve
        self.url = '/'

    def test_failey_cname(self):
        request = self.factory.get(self.url, HTTP_HOST='my.host.com')
        r = self.view(request)
        self.assertEqual(r.status_code, 404)
        self.assertEqual(request.cname, True)

    @override_settings(PRODUCTION_DOMAIN='readthedocs.org')
    @patch('proxito.views.get_project_data')
    def test_proper_subdomain(self, get_project_data):
        get_project_data.return_value = [1, 'test-slug', False, None]
        request = self.factory.get(self.url, HTTP_HOST='test-slug.readthedocs.org')
        ret = self.view(request)
        self.assertEqual(request.subdomain, True)
        self.assertEqual(request.urlconf, settings.SUBDOMAIN_URLCONF)
        self.assertEqual(request.slug, 'test-slug')

    @override_settings(PRODUCTION_DOMAIN='readthedocs.org')
    def test_wrong_subdomain(self):
        http_host = 'xyz-wrong-sub-domain-xyz.readthedocs.org'
        request = self.factory.get(self.url, HTTP_HOST=http_host)
        with self.assertRaises(Http404):
            r = self.view(request)

    @override_settings(PRODUCTION_DOMAIN='prod.readthedocs.org')
    def test_subdomain_different_length(self):
        request = self.factory.get(
            self.url, HTTP_HOST='pip.prod.readthedocs.org'
        )
        r = self.view(request)
        self.assertEqual(request.urlconf, settings.SUBDOMAIN_URLCONF)
        self.assertEqual(request.subdomain, True)
        self.assertEqual(request.slug, 'pip')

    def test_domain_object(self):
        request = self.factory.get(self.url, HTTP_HOST='docs.foobar.com')
        r = self.view(request)
        self.assertEqual(request.urlconf, settings.SUBDOMAIN_URLCONF)
        self.assertEqual(request.domain_object, True)
        self.assertEqual(request.slug, 'pip')

    def test_domain_object_missing(self):
        request = self.factory.get(self.url, HTTP_HOST='docs.foobar.com')
        r = r = self.view(request)
        self.assertEqual(r.status_code, 404)

    def test_request_header(self):
        request = self.factory.get(
            self.url, HTTP_HOST='some.random.com', HTTP_X_RTD_SLUG='pip'
        )
        r = self.view(request)
        self.assertEqual(request.urlconf, settings.SUBDOMAIN_URLCONF)
        self.assertEqual(request.cname, True)
        self.assertEqual(request.rtdheader, True)
        self.assertEqual(request.slug, 'pip')

    @override_settings(PRODUCTION_DOMAIN='readthedocs.org')
    def test_proper_cname_uppercase(self):

        request = self.factory.get(self.url, HTTP_HOST='PIP.RANDOM.COM')
        r = self.view(request)
        self.assertEqual(request.urlconf, settings.SUBDOMAIN_URLCONF)
        self.assertEqual(request.cname, True)
        self.assertEqual(request.slug, 'pip')

    def test_request_header_uppercase(self):
        request = self.factory.get(
            self.url, HTTP_HOST='some.random.com', HTTP_X_RTD_SLUG='PIP'
        )
        r = self.view(request)
        self.assertEqual(request.urlconf, settings.SUBDOMAIN_URLCONF)
        self.assertEqual(request.cname, True)
        self.assertEqual(request.rtdheader, True)
        self.assertEqual(request.slug, 'pip')

    def test_use_subdomain(self):
        domain = 'doesnt.exists.org'

        request = self.factory.get(self.url, HTTP_HOST=domain)
        res = r = self.view(request)
        self.assertIsNone(res)
        self.assertEqual(request.slug, 'pip')
        self.assertTrue(request.domain_object)

    @override_settings(PRODUCTION_DOMAIN='readthedocs.org')
    def test_long_bad_subdomain(self):
        domain = 'www.pip.readthedocs.org'
        request = self.factory.get(self.url, HTTP_HOST=domain)
        res = r = self.view(request)
        self.assertEqual(res.status_code, 400)

    @override_settings(PRODUCTION_DOMAIN='readthedocs.org')
    def test_long_subdomain(self):
        domain = 'some.long.readthedocs.org'
        request = self.factory.get(self.url, HTTP_HOST=domain)
        res = r = self.view(request)
        self.assertIsNone(res)
