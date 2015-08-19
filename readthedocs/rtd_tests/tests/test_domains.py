from django.core.cache import cache
from django.test import TestCase
from django.test.client import RequestFactory
from django.test.utils import override_settings

from django_dynamic_fixture import get

from readthedocs.core.middleware import SubdomainMiddleware
from readthedocs.projects.models import Project, Domain


class MiddlewareTests(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = SubdomainMiddleware()
        self.url = '/'
        self.old_cache_get = cache.get

    def tearDown(self):
        cache.get = self.old_cache_get

    @override_settings(PRODUCTION_DOMAIN='readthedocs.org')
    def test_cname_creation(self):
        self.assertEqual(Domain.objects.count(), 0)
        self.project = get(Project, slug='my_slug')
        cache.get = lambda x: 'my_slug'
        request = self.factory.get(self.url, HTTP_HOST='my.valid.hostname')
        self.middleware.process_request(request)
        self.assertEqual(Domain.objects.count(), 1)
        self.assertEqual(Domain.objects.first().url, 'my.valid.hostname')

    @override_settings(PRODUCTION_DOMAIN='readthedocs.org')
    def test_no_readthedocs_domain(self):
        self.assertEqual(Domain.objects.count(), 0)
        self.project = get(Project, slug='pip')
        cache.get = lambda x: 'my_slug'
        request = self.factory.get(self.url, HTTP_HOST='pip.readthedocs.org')
        self.middleware.process_request(request)
        self.assertEqual(Domain.objects.count(), 0)

    @override_settings(PRODUCTION_DOMAIN='readthedocs.org')
    def test_cname_count(self):
        self.assertEqual(Domain.objects.count(), 0)
        self.project = get(Project, slug='my_slug')
        cache.get = lambda x: 'my_slug'
        request = self.factory.get(self.url, HTTP_HOST='my.valid.hostname')

        self.middleware.process_request(request)
        self.assertEqual(Domain.objects.count(), 1)
        self.assertEqual(Domain.objects.first().url, 'my.valid.hostname')
        self.assertEqual(Domain.objects.first().count, 1)

        self.middleware.process_request(request)
        self.assertEqual(Domain.objects.count(), 1)
        self.assertEqual(Domain.objects.first().count, 2)


class ModelTests(TestCase):

    def setUp(self):
        self.project = get(Project, slug='kong')

    def test_save_parsing(self):
        domain = get(Domain, url='http://google.com')
        self.assertEqual(domain.clean_host, 'google.com')

        domain.url = 'google.com'
        self.assertEqual(domain.clean_host, 'google.com')

        domain.url = 'https://google.com'
        domain.save()
        self.assertEqual(domain.clean_host, 'google.com')

        domain.url = 'www.google.com'
        domain.save()
        self.assertEqual(domain.clean_host, 'www.google.com')
