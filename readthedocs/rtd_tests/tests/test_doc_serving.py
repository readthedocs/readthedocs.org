import os

import django_dynamic_fixture as fixture
import mock
from django.conf import settings
from django.contrib.auth.models import User
from django.http import Http404, HttpResponse
from django.test import RequestFactory, TestCase
from django.test.utils import override_settings
from django.urls import reverse
from mock import mock_open, patch

from readthedocs.builds.constants import LATEST, EXTERNAL, INTERNAL
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
        # Private projects/versions always return 404 for sitemap.xml
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

    @patch('readthedocs.core.views.static_serve')
    @patch('readthedocs.core.views.os')
    def test_custom_404_page(self, os_view_mock, static_serve_mock):
        os_view_mock.path.exists.return_value = True

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
        not_translated_public_version = fixture.get(
            Version,
            identifier='not-translated-version',
            verbose_name='not-translated-version',
            slug='not-translated-version',
            privacy_level=constants.PUBLIC,
            project=self.public,
            active=True
        )
        # This is a EXTERNAL Version
        pr_version = fixture.get(
            Version,
            identifier='pr-version',
            verbose_name='pr-version',
            slug='pr-9999',
            project=self.public,
            active=True,
            type=EXTERNAL
        )
        stable_version = fixture.get(
            Version,
            identifier='stable',
            verbose_name='stable',
            slug='stable',
            privacy_level=constants.PUBLIC,
            project=self.public,
            active=True
        )
        # This is a EXTERNAL Version
        external_version = fixture.get(
            Version,
            identifier='pr-version',
            verbose_name='pr-version',
            slug='pr-9999',
            project=self.public,
            active=True,
            type=EXTERNAL
        )
        # This also creates a Version `latest` Automatically for this project
        translation = fixture.get(
            Project,
            main_language_project=self.public,
            language='translation-es'
        )
        # sitemap hreflang should follow correct format.
        # ref: https://en.wikipedia.org/wiki/Hreflang#Common_Mistakes
        hreflang_test_translation_project = fixture.get(
            Project,
            main_language_project=self.public,
            language='zh_CN'
        )
        response = self.client.get(
            reverse('sitemap_xml'),
            HTTP_HOST='public.readthedocs.io',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/xml')
        for version in self.public.versions(manager=INTERNAL).filter(privacy_level=constants.PUBLIC):
            self.assertContains(
                response,
                self.public.get_docs_url(
                    version_slug=version.slug,
                    lang_slug=self.public.language,
                    private=False,
                ),
            )

        # PRIVATE version should not appear here
        self.assertNotContains(
            response,
            self.public.get_docs_url(
                version_slug=private_version.slug,
                lang_slug=self.public.language,
                private=True,
            ),
        )
        # The `translation` project doesn't have a version named `not-translated-version`
        # so, the sitemap should not have a doc url for
        # `not-translated-version` with `translation-es` language.
        # ie: http://public.readthedocs.io/translation-es/not-translated-version/
        self.assertNotContains(
            response,
            self.public.get_docs_url(
                version_slug=not_translated_public_version.slug,
                lang_slug=translation.language,
                private=False,
            ),
        )
        # hreflang should use hyphen instead of underscore
        # in language and country value. (zh_CN should be zh-CN)
        self.assertContains(response, 'zh-CN')

        # PR Versions should not be in the sitemap_xml.
        self.assertNotContains(
            response,
            self.public.get_docs_url(
                version_slug=external_version.slug,
                lang_slug=self.public.language,
                private=True,
            ),
        )
        # Check if STABLE version has 'priority of 1 and changefreq of weekly.
        self.assertEqual(
            response.context['versions'][0]['loc'],
            self.public.get_docs_url(
                version_slug=stable_version.slug,
                lang_slug=self.public.language,
                private=False,
            ),)
        self.assertEqual(response.context['versions'][0]['priority'], 1)
        self.assertEqual(response.context['versions'][0]['changefreq'], 'weekly')

        # Check if LATEST version has priority of 0.9 and changefreq of daily.
        self.assertEqual(
            response.context['versions'][1]['loc'],
            self.public.get_docs_url(
                version_slug='latest',
                lang_slug=self.public.language,
                private=False,
            ),)
        self.assertEqual(response.context['versions'][1]['priority'], 0.9)
        self.assertEqual(response.context['versions'][1]['changefreq'], 'daily')

    @override_settings(
        PYTHON_MEDIA=True,
        USE_SUBDOMAIN=False,
    )
    @patch(
        'readthedocs.core.views.serve._serve_symlink_docs',
        new=mock.MagicMock(return_value=HttpResponse(content_type='text/html')),
    )
    def test_user_with_multiple_projects_serve_from_same_domain(self):
        project = fixture.get(
            Project,
            main_language_project=None,
            users=[self.eric],
        )
        other_project = fixture.get(
            Project,
            main_language_project=None,
            users=[self.eric],
        )

        # Trigger the save method of the versions
        project.versions.get(slug=LATEST).save()
        other_project.versions.get(slug=LATEST).save()

        # Two projects of one owner with versions with the same slug
        self.assertIn(self.eric, project.users.all())
        self.assertIn(self.eric, other_project.users.all())
        self.assertTrue(project.versions.filter(slug=LATEST).exists())
        self.assertTrue(other_project.versions.filter(slug=LATEST).exists())

        self.client.force_login(self.eric)
        request = self.client.get(
            f'/docs/{project.slug}/en/latest/'
        )
        self.assertEqual(request.status_code, 200)
