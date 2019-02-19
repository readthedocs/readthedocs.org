
import os

import django_dynamic_fixture as fixture
import mock
from django.conf import settings
from django.contrib.auth.models import User
from django.http import Http404
from django.test import RequestFactory, TestCase
from django.test.utils import override_settings
from django.urls import reverse
from mock import mock_open, patch

from readthedocs.builds.models import Version
from readthedocs.core.middleware import SubdomainMiddleware
from readthedocs.core.views import server_error_404_subdomain
from readthedocs.core.views.serve import _serve_symlink_docs
from readthedocs.projects import constants
from readthedocs.projects.models import Project
from readthedocs.rtd_tests.base import RequestFactoryTestMixin


@override_settings(
    USE_SUBDOMAIN=False, PUBLIC_DOMAIN='public.readthedocs.org', DEBUG=False,
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
                    settings.SITE_ROOT + '/private_web_root/private',
                )

    @override_settings(PYTHON_MEDIA=False)
    def test_private_nginx_serving(self):
        with mock.patch('readthedocs.core.views.serve.os.path.exists', return_value=True):
            request = self.request(self.private_url, user=self.eric)
            r = _serve_symlink_docs(request, project=self.private, filename='/en/latest/usage.html', privacy_level='private')
            self.assertEqual(r.status_code, 200)
            self.assertEqual(
                r._headers['x-accel-redirect'][1], '/private_web_root/private/en/latest/usage.html',
            )

    @override_settings(PYTHON_MEDIA=False)
    def test_private_nginx_serving_unicode_filename(self):
        with mock.patch('readthedocs.core.views.serve.os.path.exists', return_value=True):
            request = self.request(self.private_url, user=self.eric)
            r = _serve_symlink_docs(request, project=self.private, filename='/en/latest/úñíčódé.html', privacy_level='private')
            self.assertEqual(r.status_code, 200)
            self.assertEqual(
                r._headers['x-accel-redirect'][1], '/private_web_root/private/en/latest/%C3%BA%C3%B1%C3%AD%C4%8D%C3%B3d%C3%A9.html',
            )

    @override_settings(PYTHON_MEDIA=False)
    def test_private_files_not_found(self):
        request = self.request(self.private_url, user=self.eric)
        with self.assertRaises(Http404) as exc:
            _serve_symlink_docs(request, project=self.private, filename='/en/latest/usage.html', privacy_level='private')
        self.assertTrue('private_web_root' in str(exc.exception))
        self.assertTrue('public_web_root' not in str(exc.exception))

    @override_settings(
        PYTHON_MEDIA=False,
        USE_SUBDOMAIN=True,
        PUBLIC_DOMAIN='readthedocs.io',
        ROOT_URLCONF=settings.SUBDOMAIN_URLCONF,
    )
    def test_robots_txt(self):
        self.public.versions.update(active=True, built=True)
        response = self.client.get(
            reverse('robots_txt'),
            HTTP_HOST='private.readthedocs.io',
        )
        self.assertEqual(response.status_code, 404)

        self.client.force_login(self.eric)
        response = self.client.get(
            reverse('robots_txt'),
            HTTP_HOST='private.readthedocs.io',
        )
        # Private projects/versions always return 404 for robots.txt
        self.assertEqual(response.status_code, 404)

    @override_settings(
        USE_SUBDOMAIN=True,
        PUBLIC_DOMAIN='readthedocs.io',
        ROOT_URLCONF=settings.SUBDOMAIN_URLCONF,
    )
    def test_sitemap_xml(self):
        response = self.client.get(
            reverse('sitemap_xml'),
            HTTP_HOST='private.readthedocs.io',
        )
        self.assertEqual(response.status_code, 404)

        self.client.force_login(self.eric)
        response = self.client.get(
            reverse('sitemap_xml'),
            HTTP_HOST='private.readthedocs.io',
        )
        # Private projects/versions always return 404 for robots.txt
        self.assertEqual(response.status_code, 404)


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
                    settings.SITE_ROOT + '/public_web_root/public',
                )

    @override_settings(PYTHON_MEDIA=False)
    def test_public_nginx_serving(self):
        with mock.patch('readthedocs.core.views.serve.os.path.exists', return_value=True):
            request = self.request(self.public_url, user=self.eric)
            r = _serve_symlink_docs(request, project=self.public, filename='/en/latest/usage.html', privacy_level='public')
            self.assertEqual(r.status_code, 200)
            self.assertEqual(
                r._headers['x-accel-redirect'][1], '/public_web_root/public/en/latest/usage.html',
            )

    @override_settings(PYTHON_MEDIA=False)
    def test_both_files_not_found(self):
        request = self.request(self.private_url, user=self.eric)
        with self.assertRaises(Http404) as exc:
            _serve_symlink_docs(request, project=self.private, filename='/en/latest/usage.html', privacy_level='public')
        self.assertTrue('private_web_root' not in str(exc.exception))
        self.assertTrue('public_web_root' in str(exc.exception))

    @override_settings(
        PYTHON_MEDIA=False,
        USE_SUBDOMAIN=True,
        PUBLIC_DOMAIN='readthedocs.io',
        ROOT_URLCONF=settings.SUBDOMAIN_URLCONF,
    )
    def test_default_robots_txt(self):
        self.public.versions.update(active=True, built=True)
        response = self.client.get(
            reverse('robots_txt'),
            HTTP_HOST='public.readthedocs.io',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'User-agent: *\nAllow: /\nSitemap: https://public.readthedocs.io/sitemap.xml\n')

    @override_settings(
        PYTHON_MEDIA=False,
        USE_SUBDOMAIN=True,
        PUBLIC_DOMAIN='readthedocs.io',
        ROOT_URLCONF=settings.SUBDOMAIN_URLCONF,
    )
    @patch(
        'builtins.open',
        new_callable=mock_open,
        read_data='My own robots.txt',
    )
    @patch('readthedocs.core.views.serve.os')
    def test_custom_robots_txt(self, os_mock, open_mock):
        os_mock.path.exists.return_value = True
        self.public.versions.update(active=True, built=True)
        response = self.client.get(
            reverse('robots_txt'),
            HTTP_HOST='public.readthedocs.io',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'My own robots.txt')

    @override_settings(
        PYTHON_MEDIA=False,
        USE_SUBDOMAIN=True,
        PUBLIC_DOMAIN='readthedocs.io',
        ROOT_URLCONF=settings.SUBDOMAIN_URLCONF,
    )

    @patch('readthedocs.core.views.serve.os')
    @patch('readthedocs.core.views.os')
    def test_custom_404_page(self, os_view_mock, os_serve_mock):
        os_view_mock.path.exists.return_value = True

        os_serve_mock.path.join.side_effect = os.path.join
        os_serve_mock.path.exists.return_value = True

        self.public.versions.update(active=True, built=True)

        factory = RequestFactory()
        request = factory.get(
            '/en/latest/notfoundpage.html',
            HTTP_HOST='public.readthedocs.io',
        )

        middleware = SubdomainMiddleware()
        middleware.process_request(request)
        response = server_error_404_subdomain(request)
        self.assertEqual(response.status_code, 404)
        self.assertTrue(response['X-Accel-Redirect'].endswith('/public/en/latest/404.html'))

    @override_settings(
        USE_SUBDOMAIN=True,
        PUBLIC_DOMAIN='readthedocs.io',
        ROOT_URLCONF=settings.SUBDOMAIN_URLCONF,
    )
    def test_sitemap_xml(self):
        self.public.versions.update(active=True)
        private_version = fixture.get(
            Version,
            privacy_level=constants.PRIVATE,
            project=self.public,
        )
        response = self.client.get(
            reverse('sitemap_xml'),
            HTTP_HOST='public.readthedocs.io',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/xml')
        for version in self.public.versions.filter(privacy_level=constants.PUBLIC):
            self.assertContains(
                response,
                self.public.get_docs_url(
                    version_slug=version.slug,
                    lang_slug=self.public.language,
                    private=False,
                ),
            )

        # stable is marked as PRIVATE and should not appear here
        self.assertNotContains(
            response,
            self.public.get_docs_url(
                version_slug=private_version.slug,
                lang_slug=self.public.language,
                private=True,
            ),
        )
