# -*- coding: utf-8 -*-

from __future__ import absolute_import

from django.http import Http404
from django.conf import settings
from django.core.cache import cache
from django.core.urlresolvers import get_urlconf, set_urlconf
from django.test import TestCase
from django.test.client import RequestFactory
from django.test.utils import override_settings

from django_dynamic_fixture import get

from corsheaders.middleware import CorsMiddleware
from mock import patch

from readthedocs.core.middleware import SubdomainMiddleware
from readthedocs.projects.models import Project, ProjectRelationship, Domain

from readthedocs.rtd_tests.utils import create_user


@override_settings(USE_SUBDOMAIN=True)
class MiddlewareTests(TestCase):

    urlconf_subdomain = settings.SUBDOMAIN_URLCONF

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
        self.assertEqual(request.subdomain, True)
        self.assertEqual(request.urlconf, self.urlconf_subdomain)
        self.assertEqual(request.slug, 'pip')

    @override_settings(PRODUCTION_DOMAIN='readthedocs.org')
    def test_wrong_subdomain(self):
        http_host = 'xyz-wrong-sub-domain-xyz.readthedocs.org'
        request = self.factory.get(self.url, HTTP_HOST=http_host)
        with self.assertRaises(Http404):
            self.middleware.process_request(request)

    @override_settings(PRODUCTION_DOMAIN='readthedocs.org')
    def test_restore_urlconf_after_request(self):
        """
        The urlconf attribute for the current thread
        should remain intact after each request,
        When is set to None it means 'use default from settings'.
        """
        set_urlconf(None)
        urlconf = get_urlconf()
        self.assertIsNone(urlconf)

        self.client.get(self.url, HTTP_HOST='pip.readthedocs.org')
        urlconf = get_urlconf()
        self.assertIsNone(urlconf)

        self.client.get(self.url)
        urlconf = get_urlconf()
        self.assertIsNone(urlconf)

        self.client.get(self.url, HTTP_HOST='pip.readthedocs.org')
        urlconf = get_urlconf()
        self.assertIsNone(urlconf)

    @override_settings(PRODUCTION_DOMAIN='prod.readthedocs.org')
    def test_subdomain_different_length(self):
        request = self.factory.get(self.url, HTTP_HOST='pip.prod.readthedocs.org')
        self.middleware.process_request(request)
        self.assertEqual(request.urlconf, self.urlconf_subdomain)
        self.assertEqual(request.subdomain, True)
        self.assertEqual(request.slug, 'pip')

    def test_domain_object(self):
        self.domain = get(Domain, domain='docs.foobar.com', project=self.pip)

        request = self.factory.get(self.url, HTTP_HOST='docs.foobar.com')
        self.middleware.process_request(request)
        self.assertEqual(request.urlconf, self.urlconf_subdomain)
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
        self.assertEqual(request.urlconf, self.urlconf_subdomain)
        self.assertEqual(request.cname, True)
        self.assertEqual(request.slug, 'my_slug')

    def test_request_header(self):
        request = self.factory.get(self.url, HTTP_HOST='some.random.com', HTTP_X_RTD_SLUG='pip')
        self.middleware.process_request(request)
        self.assertEqual(request.urlconf, self.urlconf_subdomain)
        self.assertEqual(request.cname, True)
        self.assertEqual(request.rtdheader, True)
        self.assertEqual(request.slug, 'pip')

    @override_settings(PRODUCTION_DOMAIN='readthedocs.org')
    def test_proper_cname_uppercase(self):
        cache.get = lambda x: x.split('.')[0]
        request = self.factory.get(self.url, HTTP_HOST='PIP.RANDOM.COM')
        self.middleware.process_request(request)
        self.assertEqual(request.urlconf, self.urlconf_subdomain)
        self.assertEqual(request.cname, True)
        self.assertEqual(request.slug, 'pip')

    def test_request_header_uppercase(self):
        request = self.factory.get(self.url, HTTP_HOST='some.random.com', HTTP_X_RTD_SLUG='PIP')
        self.middleware.process_request(request)
        self.assertEqual(request.urlconf, self.urlconf_subdomain)
        self.assertEqual(request.cname, True)
        self.assertEqual(request.rtdheader, True)
        self.assertEqual(request.slug, 'pip')

    @override_settings(USE_SUBDOMAIN=True)
    # no need to do a real dns query so patch cname_to_slug
    @patch('readthedocs.core.middleware.cname_to_slug', new=lambda x: 'doesnt')
    def test_use_subdomain_on(self):
        request = self.factory.get(self.url, HTTP_HOST='doesnt.really.matter')
        ret_val = self.middleware.process_request(request)
        self.assertIsNone(ret_val, None)


class TestCORSMiddleware(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = CorsMiddleware()
        self.url = '/api/v2/search'
        self.owner = create_user(username='owner', password='test')
        self.project = get(
            Project, slug='pip',
            users=[self.owner], privacy_level='public',
            mail_language_project=None
        )
        self.subproject = get(
            Project,
            users=[self.owner],
            privacy_level='public',
            mail_language_project=None,
        )
        self.relationship = get(
            ProjectRelationship,
            parent=self.project,
            child=self.subproject
        )
        self.domain = get(Domain, domain='my.valid.domain', project=self.project)

    def test_proper_domain(self):
        request = self.factory.get(
            self.url,
            {'project': self.project.slug},
            HTTP_ORIGIN='http://my.valid.domain',
        )
        resp = self.middleware.process_response(request, {})
        self.assertIn('Access-Control-Allow-Origin', resp)

    def test_invalid_domain(self):
        request = self.factory.get(
            self.url,
            {'project': self.project.slug},
            HTTP_ORIGIN='http://invalid.domain',
        )
        resp = self.middleware.process_response(request, {})
        self.assertNotIn('Access-Control-Allow-Origin', resp)

    def test_invalid_project(self):
        request = self.factory.get(
            self.url,
            {'project': 'foo'},
            HTTP_ORIGIN='http://my.valid.domain',
        )
        resp = self.middleware.process_response(request, {})
        self.assertNotIn('Access-Control-Allow-Origin', resp)

    def test_valid_subproject(self):
        self.assertTrue(
            Project.objects.filter(
                pk=self.project.pk,
                subprojects__child=self.subproject
            ).exists()
        )
        request = self.factory.get(
            self.url,
            {'project': self.subproject.slug},
            HTTP_ORIGIN='http://my.valid.domain',
        )
        resp = self.middleware.process_response(request, {})
        self.assertIn('Access-Control-Allow-Origin', resp)
