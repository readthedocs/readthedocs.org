import pytest
from django.test import override_settings

import django_dynamic_fixture as fixture

from readthedocs.projects.models import Domain
from .base import BaseDocServing


@override_settings(
    PUBLIC_DOMAIN='dev.readthedocs.io',
    PUBLIC_DOMAIN_USES_HTTPS=True,
)
class ProxitoHeaderTests(BaseDocServing):

    def test_redirect_headers(self):
        r = self.client.get('', HTTP_HOST='project.dev.readthedocs.io')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r['X-RTD-Redirect'], 'system')
        self.assertEqual(
            r['Location'], 'https://project.dev.readthedocs.io/en/latest/',
        )
        self.assertEqual(r['Cache-Tag'], 'project')
        self.assertEqual(r['X-RTD-Project'], 'project')
        self.assertEqual(r['X-RTD-Project-Method'], 'subdomain')
        self.assertEqual(r['X-RTD-Domain'], 'project.dev.readthedocs.io')
        self.assertIsNone(r.get('X-RTD-Version'))
        self.assertIsNone(r.get('X-RTD-Path'))

    def test_serve_headers(self):
        r = self.client.get('/en/latest/', HTTP_HOST='project.dev.readthedocs.io')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r['Cache-Tag'], 'project,project-latest')
        self.assertEqual(r['X-RTD-Domain'], 'project.dev.readthedocs.io')
        self.assertEqual(r['X-RTD-Project'], 'project')
        self.assertEqual(r['X-RTD-Project-Method'], 'subdomain')
        self.assertEqual(r['X-RTD-Version'], 'latest')
        self.assertEqual(r['X-RTD-version-Method'], 'path')
        self.assertEqual(r['X-RTD-Path'], '/proxito/media/html/project/latest/index.html')

    def test_404_headers(self):
        r = self.client.get('/foo/bar.html', HTTP_HOST='project.dev.readthedocs.io')
        self.assertEqual(r.status_code, 404)
        self.assertEqual(r['Cache-Tag'], 'project')
        self.assertEqual(r['X-RTD-Domain'], 'project.dev.readthedocs.io')
        self.assertEqual(r['X-RTD-Project'], 'project')
        self.assertEqual(r['X-RTD-Project-Method'], 'subdomain')
        self.assertEqual(r['X-RTD-version-Method'], 'path')
        self.assertIsNone(r.get('X-RTD-Version'))
        self.assertIsNone(r.get('X-RTD-Path'))

    def test_custom_domain_headers(self):
        hostname = 'docs.random.com'
        self.domain = fixture.get(
            Domain,
            project=self.project,
            domain=hostname,
        )
        r = self.client.get("/en/latest/", HTTP_HOST=hostname)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r['Cache-Tag'], 'project,project-latest')
        self.assertEqual(r['X-RTD-Domain'], self.domain.domain)
        self.assertEqual(r['X-RTD-Project'], self.project.slug)
        self.assertEqual(r['X-RTD-Project-Method'], 'cname')
        self.assertEqual(r['X-RTD-Version'], 'latest')
        self.assertEqual(r['X-RTD-version-Method'], 'path')
        self.assertEqual(r['X-RTD-Path'], '/proxito/media/html/project/latest/index.html')
