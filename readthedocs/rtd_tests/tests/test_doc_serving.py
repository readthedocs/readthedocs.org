import mock
import django_dynamic_fixture as fixture

from django.contrib.auth.models import User
from django.test import TestCase
from django.test.utils import override_settings

from readthedocs.rtd_tests.base import RequestFactoryTestMixin
from readthedocs.projects.models import Project
from readthedocs.core.views.serve import serve_symlink_docs


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


@override_settings(SERVE_PUBLIC_DOCS=False)
class TestPrivateDocs(BaseDocServing):

    @override_settings(PYTHON_MEDIA=True)
    def test_private_python_media_serving(self):
        with mock.patch('readthedocs.core.views.serve.serve') as serve_mock:
            request = self.request(self.private_url, user=self.eric)
            serve_symlink_docs(request, project=self.private, filename='en/latest/usage.html')
            serve_mock.assert_called_with(
                request,
                'en/latest/usage.html',
                '/Users/eric/projects/readthedocs.org/private_web_root/private'
            )

        r = self.client.get(self.private_url)
        self.assertEqual(r.status_code, 401)

        r = self.client.get(self.public_url)
        self.assertEqual(r.status_code, 401)

    @override_settings(PYTHON_MEDIA=False)
    def test_private_nginx_serving(self):
        request = self.request(self.private_url, user=self.eric)
        r = serve_symlink_docs(request, project=self.private, filename='en/latest/usage.html')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(
            r._headers['x-accel-redirect'][1], '/private_web_root/private/en/latest/usage.html'
        )

        r = self.client.get(self.private_url)
        self.assertEqual(r.status_code, 401)

        r = self.client.get(self.public_url)
        self.assertEqual(r.status_code, 401)


@override_settings(SERVE_PUBLIC_DOCS=True)
class TestPublicDocs(BaseDocServing):

    @override_settings(PYTHON_MEDIA=True)
    def test_public_python_media_serving(self):
        with mock.patch('readthedocs.core.views.serve.serve') as serve_mock:
            with mock.patch('readthedocs.core.views.serve.os.path.exists', return_value=True):
                request = self.request(self.public_url, user=self.eric)
                serve_symlink_docs(request, project=self.public, filename='en/latest/usage.html')
                serve_mock.assert_called_with(
                    request,
                    'en/latest/usage.html',
                    '/Users/eric/projects/readthedocs.org/public_web_root/public'
                )

        with mock.patch('readthedocs.core.views.serve.os.path.exists', return_value=True):
            r = self.client.get(self.public_url)
            self.assertEqual(r.status_code, 200)

        with mock.patch('readthedocs.core.views.serve.serve') as serve_mock:
            r = self.client.get(self.public_url)
            self.assertEqual(r.status_code, 200)
            serve_mock.assert_called_with(
                request,
                'en/latest/usage.html',
                '/Users/eric/projects/readthedocs.org/public_web_root/public'
            )

    @override_settings(PYTHON_MEDIA=False)
    def test_public_nginx_serving(self):
        with mock.patch('readthedocs.core.views.serve.os.path.exists', return_value=True):
            request = self.request(self.public_url, user=self.eric)
            r = serve_symlink_docs(request, project=self.public, filename='en/latest/usage.html')
            self.assertEqual(r.status_code, 200)
            self.assertEqual(
                r._headers['x-accel-redirect'][1], '/public_web_root/public/en/latest/usage.html'
            )

        r = self.client.get(self.public_url)
        self.assertEqual(r.status_code, 401)

        r = self.client.get(self.public_url)
        self.assertEqual(r.status_code, 401)
