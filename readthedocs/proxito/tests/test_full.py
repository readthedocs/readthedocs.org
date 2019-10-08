# Copied from .org

import os

import mock
from django.conf import settings
from django.http import HttpResponse
from django.test.utils import override_settings

from .base import BaseDocServing


@override_settings(PYTHON_MEDIA=False)
class TestFullDocServing(BaseDocServing):
    # Test the full range of possible doc URL's

    def test_subproject_serving(self):
        url = '/projects/subproject/en/latest/awesome.html'
        host = 'project.dev.readthedocs.io'
        resp = self.client.get(url, HTTP_HOST=host)
        self.assertEqual(
            resp['x-accel-redirect'], '/proxito/html/subproject/latest/awesome.html',
        )

    def test_subproject_single_version(self):
        self.subproject.single_version = True
        self.subproject.save()
        url = '/projects/subproject/awesome.html'
        host = 'project.dev.readthedocs.io'
        resp = self.client.get(url, HTTP_HOST=host)
        self.assertEqual(
            resp['x-accel-redirect'], '/proxito/html/subproject/latest/awesome.html',
        )

    def test_subproject_translation_serving(self):
        url = '/projects/subproject/es/latest/awesome.html'
        host = 'project.dev.readthedocs.io'
        resp = self.client.get(url, HTTP_HOST=host)
        self.assertEqual(
            resp['x-accel-redirect'], '/proxito/html/subproject-translation/latest/awesome.html',
        )

    def test_subproject_alias_serving(self):
        url = '/projects/this-is-an-alias/en/latest/awesome.html'
        host = 'project.dev.readthedocs.io'
        resp = self.client.get(url, HTTP_HOST=host)
        self.assertEqual(
            resp['x-accel-redirect'], '/proxito/html/subproject-alias/latest/awesome.html',
        )

    def test_translation_serving(self):
        url = '/es/latest/awesome.html'
        host = 'project.dev.readthedocs.io'
        resp = self.client.get(url, HTTP_HOST=host)
        self.assertEqual(
            resp['x-accel-redirect'], '/proxito/html/translation/latest/awesome.html',
        )

    def test_normal_serving(self):
        url = '/en/latest/awesome.html'
        host = 'project.dev.readthedocs.io'
        resp = self.client.get(url, HTTP_HOST=host)
        self.assertEqual(
            resp['x-accel-redirect'], '/proxito/html/project/latest/awesome.html',
        )

    def test_single_version_serving(self):
        self.project.single_version = True
        self.project.save()
        url = '/awesome.html'
        host = 'project.dev.readthedocs.io'
        resp = self.client.get(url, HTTP_HOST=host)
        self.assertEqual(
            resp['x-accel-redirect'], '/proxito/html/project/latest/awesome.html',
        )

    def test_single_version_serving_looks_like_normal(self):
        self.project.single_version = True
        self.project.save()
        url = '/en/stable/awesome.html'
        host = 'project.dev.readthedocs.io'
        resp = self.client.get(url, HTTP_HOST=host)
        self.assertEqual(
            resp['x-accel-redirect'], '/proxito/html/project/latest/en/stable/awesome.html',
        )

        # Invalid tests

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


class TestDocServingBackends(BaseDocServing):
    # Test that nginx and python backends both work

    @override_settings(PYTHON_MEDIA=True)
    def test_python_media_serving(self):
        with mock.patch(
                'readthedocs.proxito.views.serve', return_value=HttpResponse()) as serve_mock:
            url = '/en/latest/awesome.html'
            host = 'project.dev.readthedocs.io'
            self.client.get(url, HTTP_HOST=host)
            serve_mock.assert_called_with(
                mock.ANY,
                'html/project/latest/awesome.html',
                os.path.join(settings.SITE_ROOT, 'media'),
            )

    @override_settings(PYTHON_MEDIA=False)
    def test_nginx_media_serving(self):
        resp = self.client.get('/en/latest/awesome.html', HTTP_HOST='project.dev.readthedocs.io')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp['x-accel-redirect'], '/proxito/html/project/latest/awesome.html',
        )

    @override_settings(PYTHON_MEDIA=False)
    def test_project_nginx_serving_unicode_filename(self):
        resp = self.client.get('/en/latest/úñíčódé.html', HTTP_HOST='project.dev.readthedocs.io')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp['x-accel-redirect'],
            '/proxito/html/project/latest/%C3%BA%C3%B1%C3%AD%C4%8D%C3%B3d%C3%A9.html',
        )
