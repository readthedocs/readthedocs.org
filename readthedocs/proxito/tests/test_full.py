# Copied from .org

import os

import django_dynamic_fixture as fixture
import mock
from django.conf import settings
from django.http import HttpResponse
from django.test.utils import override_settings
from django.urls import reverse

from readthedocs.builds.constants import EXTERNAL, INTERNAL
from readthedocs.builds.models import Version
from readthedocs.projects import constants
from readthedocs.projects.models import Project

from .base import BaseDocServing


@override_settings(PYTHON_MEDIA=False)
class TestFullDocServing(BaseDocServing):
    # Test the full range of possible doc URL's

    def test_subproject_serving(self):
        url = '/projects/subproject/en/latest/awesome.html'
        host = 'project.dev.readthedocs.io'
        resp = self.client.get(url, HTTP_HOST=host)
        self.assertEqual(
            resp['x-accel-redirect'], '/proxito/media/html/subproject/latest/awesome.html',
        )

    def test_subproject_single_version(self):
        self.subproject.single_version = True
        self.subproject.save()
        url = '/projects/subproject/awesome.html'
        host = 'project.dev.readthedocs.io'
        resp = self.client.get(url, HTTP_HOST=host)
        self.assertEqual(
            resp['x-accel-redirect'], '/proxito/media/html/subproject/latest/awesome.html',
        )

    def test_subproject_translation_serving(self):
        url = '/projects/subproject/es/latest/awesome.html'
        host = 'project.dev.readthedocs.io'
        resp = self.client.get(url, HTTP_HOST=host)
        self.assertEqual(
            resp['x-accel-redirect'], '/proxito/media/html/subproject-translation/latest/awesome.html',
        )

    def test_subproject_alias_serving(self):
        url = '/projects/this-is-an-alias/en/latest/awesome.html'
        host = 'project.dev.readthedocs.io'
        resp = self.client.get(url, HTTP_HOST=host)
        self.assertEqual(
            resp['x-accel-redirect'], '/proxito/media/html/subproject-alias/latest/awesome.html',
        )

    def test_translation_serving(self):
        url = '/es/latest/awesome.html'
        host = 'project.dev.readthedocs.io'
        resp = self.client.get(url, HTTP_HOST=host)
        self.assertEqual(
            resp['x-accel-redirect'], '/proxito/media/html/translation/latest/awesome.html',
        )

    def test_normal_serving(self):
        url = '/en/latest/awesome.html'
        host = 'project.dev.readthedocs.io'
        resp = self.client.get(url, HTTP_HOST=host)
        self.assertEqual(
            resp['x-accel-redirect'], '/proxito/media/html/project/latest/awesome.html',
        )

    def test_single_version_serving(self):
        self.project.single_version = True
        self.project.save()
        url = '/awesome.html'
        host = 'project.dev.readthedocs.io'
        resp = self.client.get(url, HTTP_HOST=host)
        self.assertEqual(
            resp['x-accel-redirect'], '/proxito/media/html/project/latest/awesome.html',
        )

    def test_single_version_serving_looks_like_normal(self):
        self.project.single_version = True
        self.project.save()
        url = '/en/stable/awesome.html'
        host = 'project.dev.readthedocs.io'
        resp = self.client.get(url, HTTP_HOST=host)
        self.assertEqual(
            resp['x-accel-redirect'], '/proxito/media/html/project/latest/en/stable/awesome.html',
        )

    @override_settings(
        RTD_EXTERNAL_VERSION_DOMAIN='dev.readthedocs.build',
    )
    def test_single_version_external_serving(self):
        self.project.single_version = True
        self.project.save()
        fixture.get(
            Version,
            verbose_name='10',
            slug='10',
            type=EXTERNAL,
            active=True,
            project=self.project,
        )
        url = '/awesome.html'
        host = 'project--10.dev.readthedocs.build'
        resp = self.client.get(url, HTTP_HOST=host)
        self.assertEqual(
            resp['x-accel-redirect'], '/proxito/media/external/html/project/10/awesome.html',
        )

    @override_settings(
        RTD_EXTERNAL_VERSION_DOMAIN='dev.readthedocs.build',
    )
    def test_external_version_serving(self):
        fixture.get(
            Version,
            verbose_name='10',
            slug='10',
            type=EXTERNAL,
            active=True,
            project=self.project,
        )
        url = '/awesome.html'
        host = 'project--10.dev.readthedocs.build'
        resp = self.client.get(url, HTTP_HOST=host)
        self.assertEqual(
            resp['x-accel-redirect'], '/proxito/media/external/html/project/10/awesome.html',
        )

        # Invalid tests

    @override_settings(
        RTD_EXTERNAL_VERSION_DOMAIN='dev.readthedocs.build',
    )
    def test_invalid_domain_for_external_version_serving(self):
        fixture.get(
            Version,
            verbose_name='10',
            slug='10',
            type=EXTERNAL,
            active=True,
            project=self.project,
        )
        url = '/html/project/10/awesome.html'
        host = 'project.dev.readthedocs.io'
        resp = self.client.get(url, HTTP_HOST=host)
        self.assertEqual(resp.status_code, 404)

    def test_invalid_language_for_project_with_versions(self):
        url = '/foo/latest/awesome.html'
        host = 'project.dev.readthedocs.io'
        resp = self.client.get(url, HTTP_HOST=host)
        self.assertEqual(resp.status_code, 404)

    def test_invalid_translation_for_project_with_versions(self):
        url = '/cs/latest/awesome.html'
        host = 'project.dev.readthedocs.io'
        resp = self.client.get(url, HTTP_HOST=host)
        self.assertEqual(resp.status_code, 404)

    def test_invalid_subproject(self):
        url = '/projects/doesnt-exist/foo.html'
        host = 'project.dev.readthedocs.io'
        resp = self.client.get(url, HTTP_HOST=host)
        self.assertEqual(resp.status_code, 404)

    # https://github.com/readthedocs/readthedocs.org/pull/6226/files/596aa85a4886407f0eb65233ebf9c38ee3e8d485#r332445803
    def test_valid_project_as_invalid_subproject(self):
        url = '/projects/translation/es/latest/foo.html'
        host = 'project.dev.readthedocs.io'
        resp = self.client.get(url, HTTP_HOST=host)
        self.assertEqual(resp.status_code, 404)


class TestDocServingBackends(BaseDocServing):
    # Test that nginx and python backends both work

    @override_settings(PYTHON_MEDIA=True)
    def test_python_media_serving(self):
        with mock.patch(
                'readthedocs.proxito.views.mixins.serve', return_value=HttpResponse()) as serve_mock:
            url = '/en/latest/awesome.html'
            host = 'project.dev.readthedocs.io'
            self.client.get(url, HTTP_HOST=host)
            serve_mock.assert_called_with(
                mock.ANY,
                '/media/html/project/latest/awesome.html',
                os.path.join(settings.SITE_ROOT, 'media'),
            )

    @override_settings(PYTHON_MEDIA=False)
    def test_nginx_media_serving(self):
        resp = self.client.get('/en/latest/awesome.html', HTTP_HOST='project.dev.readthedocs.io')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp['x-accel-redirect'], '/proxito/media/html/project/latest/awesome.html',
        )

    @override_settings(PYTHON_MEDIA=False)
    def test_project_nginx_serving_unicode_filename(self):
        resp = self.client.get('/en/latest/úñíčódé.html', HTTP_HOST='project.dev.readthedocs.io')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp['x-accel-redirect'],
            '/proxito/media/html/project/latest/%C3%BA%C3%B1%C3%AD%C4%8D%C3%B3d%C3%A9.html',
        )


@override_settings(
    PYTHON_MEDIA=False,
    PUBLIC_DOMAIN='readthedocs.io',
    RTD_BUILD_MEDIA_STORAGE='readthedocs.rtd_tests.storage.BuildMediaFileSystemStorageTest',
)
class TestAdditionalDocViews(BaseDocServing):
    # Test that robots.txt and sitemap.xml work

    @mock.patch('readthedocs.proxito.views.serve.get_storage_class')
    def test_default_robots_txt(self, storage_mock):
        storage_mock()().exists.return_value = False
        self.project.versions.update(active=True, built=True)
        response = self.client.get(
            reverse('robots_txt'),
            HTTP_HOST='project.readthedocs.io',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.content,
            b'User-agent: *\nAllow: /\nSitemap: https://project.readthedocs.io/sitemap.xml\n'
        )

    def test_custom_robots_txt(self):
        self.project.versions.update(active=True, built=True)
        response = self.client.get(
            reverse('robots_txt'),
            HTTP_HOST='project.readthedocs.io',
        )
        self.assertEqual(
            response['x-accel-redirect'], '/proxito/media/html/project/latest/robots.txt',
        )

    def test_directory_indexes(self):
        self.project.versions.update(active=True, built=True)
        # Confirm we've serving from storage for the `index-exists/index.html` file
        response = self.client.get(
            reverse('proxito_404_handler', kwargs={'proxito_path': '/en/latest/index-exists'}),
            HTTP_HOST='project.readthedocs.io',
        )
        self.assertEqual(
            response.status_code, 302
        )
        self.assertEqual(
            response['location'], '/en/latest/index-exists/',
        )

    def test_versioned_no_slash(self):
        self.project.versions.update(active=True, built=True)
        response = self.client.get(
            reverse('proxito_404_handler', kwargs={'proxito_path': '/en/latest'}),
            HTTP_HOST='project.readthedocs.io',
        )
        self.assertEqual(
            response.status_code, 302
        )
        self.assertEqual(
            response['location'], '/en/latest/',
        )

    @mock.patch('readthedocs.proxito.views.serve.get_storage_class')
    def test_directory_indexes_readme_serving(self, storage_mock):
        self.project.versions.update(active=True, built=True)

        storage_mock()().exists.side_effect = [False, True]
        # Confirm we've serving from storage for the `index-exists/index.html` file
        response = self.client.get(
            reverse('proxito_404_handler', kwargs={'proxito_path': '/en/latest/readme-exists'}),
            HTTP_HOST='project.readthedocs.io',
        )
        self.assertEqual(
            response.status_code, 302
        )
        self.assertEqual(
            response['location'], '/en/latest/readme-exists/README.html',
        )

    def test_directory_indexes_get_args(self):
        self.project.versions.update(active=True, built=True)
        # Confirm we've serving from storage for the `index-exists/index.html` file
        response = self.client.get(
            reverse('proxito_404_handler', kwargs={'proxito_path': '/en/latest/index-exists?foo=bar'}),
            HTTP_HOST='project.readthedocs.io',
        )
        self.assertEqual(
            response.status_code, 302
        )
        self.assertEqual(
            response['location'], '/en/latest/index-exists/?foo=bar',
        )

    @mock.patch('readthedocs.proxito.views.serve.get_storage_class')
    def test_404_storage_serves_404(self, storage_mock):
        self.project.versions.update(active=True, built=True)

        storage_mock()().exists.side_effect = [False, False, True]
        response = self.client.get(
            reverse('proxito_404_handler', kwargs={'proxito_path': '/en/fancy-version/not-found'}),
            HTTP_HOST='project.readthedocs.io',
        )
        storage_mock()().exists.assert_has_calls(
            [
                mock.call('html/project/fancy-version/not-found/index.html'),
                mock.call('html/project/fancy-version/not-found/README.html'),
                mock.call('html/project/fancy-version/404.html'),
            ]
        )
        self.assertEqual(
            response.status_code, 404
        )

    @mock.patch('readthedocs.proxito.views.serve.get_storage_class')
    def test_404_storage_paths_checked(self, storage_mock):
        self.project.versions.update(active=True, built=True)
        storage_mock()().exists.return_value = False
        self.client.get(
            reverse('proxito_404_handler', kwargs={'proxito_path': '/en/fancy-version/not-found'}),
            HTTP_HOST='project.readthedocs.io',
        )
        storage_mock()().exists.assert_has_calls(
            [
                mock.call('html/project/fancy-version/not-found/index.html'),
                mock.call('html/project/fancy-version/not-found/README.html'),
                mock.call('html/project/fancy-version/404.html'),
                mock.call('html/project/fancy-version/404/index.html'),
                mock.call('html/project/latest/404.html'),
                mock.call('html/project/latest/404/index.html')
            ]
        )

    def test_sitemap_xml(self):
        self.project.versions.update(active=True)
        private_version = fixture.get(
            Version,
            privacy_level=constants.PRIVATE,
            project=self.project,
        )
        not_translated_public_version = fixture.get(
            Version,
            identifier='not-translated-version',
            verbose_name='not-translated-version',
            slug='not-translated-version',
            privacy_level=constants.PUBLIC,
            project=self.project,
            active=True
        )
        stable_version = fixture.get(
            Version,
            identifier='stable',
            verbose_name='stable',
            slug='stable',
            privacy_level=constants.PUBLIC,
            project=self.project,
            active=True
        )
        # This is a EXTERNAL Version
        external_version = fixture.get(
            Version,
            identifier='pr-version',
            verbose_name='pr-version',
            slug='pr-9999',
            project=self.project,
            active=True,
            type=EXTERNAL
        )
        # This also creates a Version `latest` Automatically for this project
        translation = fixture.get(
            Project,
            main_language_project=self.project,
            language='translation-es',
            privacy_level=constants.PUBLIC,
        )
        translation.versions.update(privacy_level=constants.PUBLIC)
        # sitemap hreflang should follow correct format.
        # ref: https://en.wikipedia.org/wiki/Hreflang#Common_Mistakes
        hreflang_test_translation_project = fixture.get(
            Project,
            main_language_project=self.project,
            language='zh_CN',
            privacy_level=constants.PUBLIC,
        )
        hreflang_test_translation_project.versions.update(
            privacy_level=constants.PUBLIC,
        )

        response = self.client.get(
            reverse('sitemap_xml'),
            HTTP_HOST='project.readthedocs.io',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/xml')
        for version in self.project.versions(manager=INTERNAL).filter(privacy_level=constants.PUBLIC):
            self.assertContains(
                response,
                self.project.get_docs_url(
                    version_slug=version.slug,
                    lang_slug=self.project.language,
                    private=False,
                ),
            )

        # PRIVATE version should not appear here
        self.assertNotContains(
            response,
            self.project.get_docs_url(
                version_slug=private_version.slug,
                lang_slug=self.project.language,
                private=True,
            ),
        )
        # The `translation` project doesn't have a version named `not-translated-version`
        # so, the sitemap should not have a doc url for
        # `not-translated-version` with `translation-es` language.
        # ie: http://project.readthedocs.io/translation-es/not-translated-version/
        self.assertNotContains(
            response,
            self.project.get_docs_url(
                version_slug=not_translated_public_version.slug,
                lang_slug=translation.language,
                private=False,
            ),
        )
        # hreflang should use hyphen instead of underscore
        # in language and country value. (zh_CN should be zh-CN)
        self.assertContains(response, 'zh-CN')

        # External Versions should not be in the sitemap_xml.
        self.assertNotContains(
            response,
            self.project.get_docs_url(
                version_slug=external_version.slug,
                lang_slug=self.project.language,
                private=True,
            ),
        )

        # Check if STABLE version has 'priority of 1 and changefreq of weekly.
        self.assertEqual(
            response.context['versions'][0]['loc'],
            self.project.get_docs_url(
                version_slug=stable_version.slug,
                lang_slug=self.project.language,
                private=False,
            ),)
        self.assertEqual(response.context['versions'][0]['priority'], 1)
        self.assertEqual(response.context['versions'][0]['changefreq'], 'weekly')

        # Check if LATEST version has priority of 0.9 and changefreq of daily.
        self.assertEqual(
            response.context['versions'][1]['loc'],
            self.project.get_docs_url(
                version_slug='latest',
                lang_slug=self.project.language,
                private=False,
            ),)
        self.assertEqual(response.context['versions'][1]['priority'], 0.9)
        self.assertEqual(response.context['versions'][1]['changefreq'], 'daily')
