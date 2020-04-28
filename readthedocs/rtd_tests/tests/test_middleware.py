from corsheaders.middleware import CorsMiddleware
from django.conf import settings
from django.contrib.auth.middleware import AuthenticationMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import Http404
from django.http import HttpResponse
from django.test import TestCase
from django.test.client import RequestFactory
from django.test.utils import override_settings
from django.urls.base import get_urlconf, set_urlconf
from django_dynamic_fixture import get

from readthedocs.core.middleware import ReadTheDocsSessionMiddleware
from readthedocs.projects.models import Domain, Project, ProjectRelationship
from readthedocs.rtd_tests.utils import create_user


class TestCORSMiddleware(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = CorsMiddleware()
        self.url = '/api/v2/search'
        self.owner = create_user(username='owner', password='test')
        self.project = get(
            Project, slug='pip',
            users=[self.owner], privacy_level='public',
            main_language_project=None,
        )
        self.subproject = get(
            Project,
            users=[self.owner],
            privacy_level='public',
            main_language_project=None,
        )
        self.relationship = get(
            ProjectRelationship,
            parent=self.project,
            child=self.subproject,
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

    def test_valid_subproject(self):
        self.assertTrue(
            Project.objects.filter(
                pk=self.project.pk,
                subprojects__child=self.subproject,
            ).exists(),
        )
        request = self.factory.get(
            self.url,
            {'project': self.subproject.slug},
            HTTP_ORIGIN='http://my.valid.domain',
        )
        resp = self.middleware.process_response(request, {})
        self.assertIn('Access-Control-Allow-Origin', resp)

    def test_apiv2_endpoint_allowed(self):
        request = self.factory.get(
            '/api/v2/version/',
            {'project__slug': self.project.slug, 'active': True},
            HTTP_ORIGIN='http://my.valid.domain',
        )
        resp = self.middleware.process_response(request, {})
        self.assertIn('Access-Control-Allow-Origin', resp)

    def test_apiv2_endpoint_not_allowed(self):
        request = self.factory.get(
            '/api/v2/version/',
            {'project__slug': self.project.slug, 'active': True},
            HTTP_ORIGIN='http://invalid.domain',
        )
        resp = self.middleware.process_response(request, {})
        self.assertNotIn('Access-Control-Allow-Origin', resp)

        # POST is not allowed
        request = self.factory.post(
            '/api/v2/version/',
            {'project__slug': self.project.slug, 'active': True},
            HTTP_ORIGIN='http://my.valid.domain',
        )
        resp = self.middleware.process_response(request, {})
        self.assertNotIn('Access-Control-Allow-Origin', resp)


class TestSessionMiddleware(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = ReadTheDocsSessionMiddleware()

        self.user = create_user(username='owner', password='test')

    def test_fallback_cookie(self):
        request = self.factory.get('/')
        response = HttpResponse()
        self.middleware.process_request(request)
        request.session['test'] = 'value'
        response = self.middleware.process_response(request, response)

        self.assertTrue(settings.SESSION_COOKIE_NAME in response.cookies)
        self.assertTrue(self.middleware.cookie_name_fallback in response.cookies)

    def test_main_cookie_samesite_none(self):
        request = self.factory.get('/')
        response = HttpResponse()
        self.middleware.process_request(request)
        request.session['test'] = 'value'
        response = self.middleware.process_response(request, response)

        self.assertEqual(response.cookies[settings.SESSION_COOKIE_NAME]['samesite'], 'None')
        self.assertEqual(response.cookies[self.middleware.cookie_name_fallback]['samesite'], '')
