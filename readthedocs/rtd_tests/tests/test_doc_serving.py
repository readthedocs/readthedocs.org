from __future__ import absolute_import
import mock
import django_dynamic_fixture as fixture

from django.contrib.auth.models import User
from django.test import TestCase
from django.test.utils import override_settings
from django.http import Http404
from django.conf import settings

from readthedocs.rtd_tests.base import RequestFactoryTestMixin
from readthedocs.projects import constants
from readthedocs.projects.models import Project
from readthedocs.core.views.serve import _serve_symlink_docs


@override_settings(
    USE_SUBDOMAIN=False, PUBLIC_DOMAIN='public.readthedocs.org', DEBUG=False
)
class BaseDocServing(RequestFactoryTestMixin, TestCase):

    def setUp(self):
        self.eric = fixture.get(User, username='eric')
        self.eric.set_password('eric')
        self.eric.save()
        self.public = fixture.get(Project, slug='public', main_language_project=None)
        self.private = fixture.get(
            Project, slug='private', privacy_level='private',
            version_privacy_level='private', users=[self.eric],
        )
        self.private_url = '/docs/private/en/latest/usage.html'
        self.public_url = '/docs/public/en/latest/usage.html'


@override_settings(SERVE_DOCS=[constants.PRIVATE])
class TestPrivateDocs(BaseDocServing):

    @override_settings(PYTHON_MEDIA=True)
    def test_private_python_media_serving(self):
        with mock.patch('readthedocs.core.views.serve.serve') as serve_mock:
            with mock.patch('readthedocs.core.views.serve.os.path.exists', return_value=True):
                request = self.request(self.private_url, user=self.eric)
                _serve_symlink_docs(request, project=self.private, filename='/en/latest/usage.html', privacy_level='private')
                serve_mock.assert_called_with(
                    request,
                    'en/latest/usage.html',
                    settings.SITE_ROOT + '/private_web_root/private'
                )

    @override_settings(PYTHON_MEDIA=False)
    def test_private_nginx_serving(self):
        with mock.patch('readthedocs.core.views.serve.os.path.exists', return_value=True):
            request = self.request(self.private_url, user=self.eric)
            r = _serve_symlink_docs(request, project=self.private, filename='/en/latest/usage.html', privacy_level='private')
            self.assertEqual(r.status_code, 200)
            self.assertEqual(
                r._headers['x-accel-redirect'][1], '/private_web_root/private/en/latest/usage.html'
            )

    @override_settings(PYTHON_MEDIA=False)
    def test_private_files_not_found(self):
        request = self.request(self.private_url, user=self.eric)
        with self.assertRaises(Http404) as exc:
            _serve_symlink_docs(request, project=self.private, filename='/en/latest/usage.html', privacy_level='private')
        self.assertTrue('private_web_root' in str(exc.exception))
        self.assertTrue('public_web_root' not in str(exc.exception))


@override_settings(SERVE_DOCS=[constants.PRIVATE, constants.PUBLIC])
class TestPublicDocs(BaseDocServing):

    @override_settings(PYTHON_MEDIA=True)
    def test_public_python_media_serving(self):
        with mock.patch('readthedocs.core.views.serve.serve') as serve_mock:
            with mock.patch('readthedocs.core.views.serve.os.path.exists', return_value=True):
                request = self.request(self.public_url, user=self.eric)
                _serve_symlink_docs(request, project=self.public, filename='/en/latest/usage.html', privacy_level='public')
                serve_mock.assert_called_with(
                    request,
                    'en/latest/usage.html',
                    settings.SITE_ROOT + '/public_web_root/public'
                )

    @override_settings(PYTHON_MEDIA=False)
    def test_public_nginx_serving(self):
        with mock.patch('readthedocs.core.views.serve.os.path.exists', return_value=True):
            request = self.request(self.public_url, user=self.eric)
            r = _serve_symlink_docs(request, project=self.public, filename='/en/latest/usage.html', privacy_level='public')
            self.assertEqual(r.status_code, 200)
            self.assertEqual(
                r._headers['x-accel-redirect'][1], '/public_web_root/public/en/latest/usage.html'
            )

    @override_settings(PYTHON_MEDIA=False)
    def test_both_files_not_found(self):
        request = self.request(self.private_url, user=self.eric)
        with self.assertRaises(Http404) as exc:
            _serve_symlink_docs(request, project=self.private, filename='/en/latest/usage.html', privacy_level='public')
        self.assertTrue('private_web_root' not in str(exc.exception))
        self.assertTrue('public_web_root' in str(exc.exception))
