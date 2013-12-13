from django.http import Http404
from django.core.cache import cache
from django.utils import unittest
from django.test.client import RequestFactory
from django.test.utils import override_settings

from core.middleware import SubdomainMiddleware


class MiddlewareTests(unittest.TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = SubdomainMiddleware()
        self.url = '/'

    def test_failey_cname(self):
        request = self.factory.get(self.url, HTTP_HOST='my.host.com')
        with self.assertRaises(Http404):
            self.middleware.process_request(request)
        self.assertEqual(request.cname, True)

    def test_proper_subdomain(self):
        request = self.factory.get(self.url, HTTP_HOST='pip.readthedocs.org')
        self.middleware.process_request(request)
        self.assertEqual(request.urlconf, 'core.subdomain_urls')
        self.assertEqual(request.subdomain, True)
        self.assertEqual(request.slug, 'pip')

    def test_proper_cname(self):
        cache.get = lambda x: 'my_slug'
        request = self.factory.get(self.url, HTTP_HOST='my.valid.homename')
        self.middleware.process_request(request)
        self.assertEqual(request.urlconf, 'core.subdomain_urls')
        self.assertEqual(request.cname, True)
        self.assertEqual(request.slug, 'my_slug')

    def test_request_header(self):
        request = self.factory.get(self.url, HTTP_HOST='some.random.com', HTTP_X_RTD_SLUG='pip')
        self.middleware.process_request(request)
        self.assertEqual(request.urlconf, 'core.subdomain_urls')
        self.assertEqual(request.cname, True)
        self.assertEqual(request.rtdheader, True)
        self.assertEqual(request.slug, 'pip')

    @override_settings(DEBUG=True)
    def test_debug_on(self):
        request = self.factory.get(self.url, HTTP_HOST='doesnt.really.matter')
        ret_val = self.middleware.process_request(request)
        self.assertEqual(ret_val, None)
