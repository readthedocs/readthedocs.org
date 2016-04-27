from django.http import Http404
from django.core.cache import cache
from django.test import TestCase
from django.test.client import RequestFactory
from django.test.utils import override_settings

from django_dynamic_fixture import get, new

from readthedocs.core.middleware import SubdomainMiddleware
from readthedocs.projects.models import Project, Domain

# Once this util gets merged remove them here
# from readthedocs.rtd_tests.utils import create_user
from django.contrib.auth.models import User


def create_user(username, password):
    user = new(User, username=username)
    user.set_password(password)
    user.save()
    return user


@override_settings(USE_SUBDOMAIN=True)
class MiddlewareTests(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = SubdomainMiddleware()
        self.url = '/'
        self.owner = create_user(username='owner', password='test')
        self.pip = get(Project, slug='pip', users=[self.owner], privacy_level='public')

    def test_failey_cname(self):
        request = self.factory.get(self.url, HTTP_HOST='my.host.com')
        with self.assertRaises(Http404):
            self.middleware.process_request(request)
        self.assertEqual(request.cname, True)

    @override_settings(PRODUCTION_DOMAIN='readthedocs.org')
    def test_proper_subdomain(self):
        request = self.factory.get(self.url, HTTP_HOST='pip.readthedocs.org')
        self.middleware.process_request(request)
        self.assertEqual(request.urlconf, 'readthedocs.core.subdomain_urls')
        self.assertEqual(request.subdomain, True)
        self.assertEqual(request.slug, 'pip')

    @override_settings(PRODUCTION_DOMAIN='prod.readthedocs.org')
    def test_subdomain_different_length(self):
        request = self.factory.get(self.url, HTTP_HOST='pip.prod.readthedocs.org')
        self.middleware.process_request(request)
        self.assertEqual(request.urlconf, 'readthedocs.core.subdomain_urls')
        self.assertEqual(request.subdomain, True)
        self.assertEqual(request.slug, 'pip')

    def test_domain_object(self):
        self.domain = get(Domain, domain='docs.foobar.com', project=self.pip)

        request = self.factory.get(self.url, HTTP_HOST='docs.foobar.com')
        self.middleware.process_request(request)
        self.assertEqual(request.urlconf, 'readthedocs.core.subdomain_urls')
        self.assertEqual(request.domain_object, True)
        self.assertEqual(request.slug, 'pip')

    def test_domain_object_missing(self):
        self.domain = get(Domain, domain='docs.foobar2.com', project=self.pip)
        request = self.factory.get(self.url, HTTP_HOST='docs.foobar.com')
        with self.assertRaises(Http404):
            self.middleware.process_request(request)

    def test_proper_cname(self):
        cache.get = lambda x: 'my_slug'
        request = self.factory.get(self.url, HTTP_HOST='my.valid.homename')
        self.middleware.process_request(request)
        self.assertEqual(request.urlconf, 'readthedocs.core.subdomain_urls')
        self.assertEqual(request.cname, True)
        self.assertEqual(request.slug, 'my_slug')

    def test_request_header(self):
        request = self.factory.get(self.url, HTTP_HOST='some.random.com', HTTP_X_RTD_SLUG='pip')
        self.middleware.process_request(request)
        self.assertEqual(request.urlconf, 'readthedocs.core.subdomain_urls')
        self.assertEqual(request.cname, True)
        self.assertEqual(request.rtdheader, True)
        self.assertEqual(request.slug, 'pip')

    @override_settings(PRODUCTION_DOMAIN='readthedocs.org')
    def test_proper_cname_uppercase(self):
        cache.get = lambda x: x.split('.')[0]
        request = self.factory.get(self.url, HTTP_HOST='PIP.RANDOM.COM')
        self.middleware.process_request(request)
        self.assertEqual(request.urlconf, 'readthedocs.core.subdomain_urls')
        self.assertEqual(request.cname, True)
        self.assertEqual(request.slug, 'pip')

    def test_request_header_uppercase(self):
        request = self.factory.get(self.url, HTTP_HOST='some.random.com', HTTP_X_RTD_SLUG='PIP')
        self.middleware.process_request(request)
        self.assertEqual(request.urlconf, 'readthedocs.core.subdomain_urls')
        self.assertEqual(request.cname, True)
        self.assertEqual(request.rtdheader, True)
        self.assertEqual(request.slug, 'pip')

    @override_settings(USE_SUBDOMAIN=True)
    def test_use_subdomain_on(self):
        request = self.factory.get(self.url, HTTP_HOST='doesnt.really.matter')
        ret_val = self.middleware.process_request(request)
        self.assertEqual(ret_val, None)
