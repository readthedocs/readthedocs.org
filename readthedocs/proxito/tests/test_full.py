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
        host = 'private.dev.readthedocs.io'
        resp = self.client.get(url, HTTP_HOST=host)
        self.assertEqual(
            resp['x-accel-redirect'], '/proxito/html/subproject/latest/awesome.html',
        )

    def test_subproject_single_version(self):
        self.subproject.single_version = True
        self.subproject.save()
        url = '/projects/subproject/awesome.html'
        host = 'private.dev.readthedocs.io'
        resp = self.client.get(url, HTTP_HOST=host)
        self.assertEqual(
            resp['x-accel-redirect'], '/proxito/html/subproject/latest/awesome.html',
        )


class TestDocServingBackends(BaseDocServing):
    # Test that nginx and python backends both work

    @override_settings(PYTHON_MEDIA=True)
    def test_python_media_serving(self):
        with mock.patch('readthedocs.proxito.views.serve', return_value=HttpResponse()) as serve_mock:
            resp = self.client.get('/en/latest/awesome.html',
                                   HTTP_HOST='private.dev.readthedocs.io')
            serve_mock.assert_called_with(
                mock.ANY,
                'html/private/latest/awesome.html',
                os.path.join(settings.SITE_ROOT, 'media'),
            )

    @override_settings(PYTHON_MEDIA=False)
    def test_nginx_media_serving(self):
        resp = self.client.get('/en/latest/awesome.html', HTTP_HOST='private.dev.readthedocs.io')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp['x-accel-redirect'], '/proxito/html/private/latest/awesome.html',
        )

    @override_settings(PYTHON_MEDIA=False)
    def test_private_nginx_serving_unicode_filename(self):
        resp = self.client.get('/en/latest/úñíčódé.html', HTTP_HOST='private.dev.readthedocs.io')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp['x-accel-redirect'], '/proxito/html/private/latest/%C3%BA%C3%B1%C3%AD%C4%8D%C3%B3d%C3%A9.html',
        )
