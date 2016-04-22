from django.test import TestCase
from django.test.utils import override_settings

import django_dynamic_fixture as fixture

from readthedocs.projects.models import Project


@override_settings(
    USE_SUBDOMAIN=True, PUBLIC_DOMAIN='public.readthedocs.org', SERVE_PUBLIC_DOCS=True
)
class RedirectSingleVersionTests(TestCase):

    def setUp(self):
        self.pip = fixture.get(Project, slug='pip', single_version=True, main_language_project=None)

    def test_proper_single_version_url_full_with_filename(self):
        with override_settings(USE_SUBDOMAIN=False):
            r = self.client.get('/docs/pip/usage.html')
            self.assertEqual(r.status_code, 200)

    def test_improper_single_version_url_nonexistent_project(self):
        with override_settings(USE_SUBDOMAIN=False):
            r = self.client.get('/docs/nonexistent/blah.html')
            self.assertEqual(r.status_code, 404)

    def test_proper_single_version_url_subdomain(self):
        r = self.client.get('/usage.html',
                            HTTP_HOST='pip.public.readthedocs.org')
        self.assertEqual(r.status_code, 200)

    def test_improper_single_version_url_subdomain(self):
        r = self.client.get('/blah.html',
                            HTTP_HOST='nonexistent.public.readthedocs.org')
        self.assertEqual(r.status_code, 404)

    def test_docs_url_generation(self):
        with override_settings(USE_SUBDOMAIN=False):
            self.assertEqual(self.pip.get_docs_url(),
                             'http://public.readthedocs.org/docs/pip/')
        with override_settings(USE_SUBDOMAIN=True):
            self.assertEqual(self.pip.get_docs_url(),
                             'http://pip.public.readthedocs.org/')

        self.pip.single_version = False
        with override_settings(USE_SUBDOMAIN=False):
            self.assertEqual(self.pip.get_docs_url(),
                             'http://public.readthedocs.org/docs/pip/en/latest/')
        with override_settings(USE_SUBDOMAIN=True):
            self.assertEqual(self.pip.get_docs_url(),
                             'http://pip.public.readthedocs.org/en/latest/')
